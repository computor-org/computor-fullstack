create sequence public.user_unique_fs_number_seq start with 1 increment by 1 no minvalue no maxvalue cache 1;

create type public.user_type as enum ('user', 'db','token');

create table if not exists public.user
(
    given_name       varchar(255),
    family_name      varchar(255),
    email            varchar(320),
    user_type        public.user_type not null default 'user',
    fs_number        bigint           not null default nextval('public.user_unique_fs_number_seq'),
    auth_token       varchar(512),
    token_expiration timestamptz,
    username         varchar(255),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null,
    primary key (id)
) inherits (interfaces.number, interfaces.resource, interfaces.archivable)
  using heap;

create unique index user_username_key on public.user (username) where archived_at is null;
create unique index user_email_key on public.user (email) where archived_at is null;
create unique index user_number_key on public.user (number) where archived_at is null;

alter table public.user
    add constraint user_token_condition check (
        (user_type = 'token' and auth_token is not null and token_expiration is not null) or user_type != 'token' );
alter table public.user
    add constraint user_username_condition check ( (user_type = 'db' and username is not null) or user_type != 'token' );

create or replace function public.user_before_insert_or_update() returns TRIGGER as
$$
begin
    if NEW.auth_token is not null then NEW.auth_token := crypt(NEW.auth_token, gen_salt('bf', 12)); end if;
    return NEW;
end;
$$ language plpgsql;

create trigger update_timestamps
    before insert or update
    on public.user
    for each row
execute function public.ctutor_update_timestamps();

create trigger before_insert_or_update
    before insert or update
    on public.user
    for each row
execute function public.user_before_insert_or_update();



create table public.profile
(
    nickname varchar(255),
    bio      varchar(16384),
    url      varchar(2048),
    user_id  uuid not null,
    foreign key (user_id) references public.user (id) on update restrict on delete cascade,
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null,
    primary key (id)
) inherits (interfaces.resource, interfaces.avatar)
  using heap;

create trigger update_timestamps
    before insert or update
    on public.profile
    for each row
execute function public.ctutor_update_timestamps();

create unique index profile_nickname_key on public.profile (nickname);
create unique index profile_user_id_idx on public.profile using btree (user_id);

create table public.student_profile
(
    student_id    varchar(255),
    student_email varchar(320),
    user_id       uuid not null,
    foreign key (user_id) references public.user (id) on update restrict on delete cascade,
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null,
    primary key (id)
) inherits (interfaces.resource)
  using heap;

create trigger update_timestamps
    before insert or update
    on public.student_profile
    for each row
execute function public.ctutor_update_timestamps();

create unique index student_profile_user_id_idx on public.student_profile using btree (user_id);
create unique index student_profile_student_id_key on public.student_profile (student_id);
create unique index student_profile_student_email_key on public.student_profile (student_email);

create table public.account
(
    provider            varchar(255) not null,
    type                varchar(63)  not null,
    provider_account_id varchar(255) not null,
    user_id             uuid         not null,
    foreign key (user_id) references public.user (id) on update restrict on delete cascade,
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null,
    primary key (id)
) inherits (interfaces.resource)
  using heap;

create trigger update_timestamps
    before insert or update
    on public.account
    for each row
execute function public.ctutor_update_timestamps();

create unique index account_provider_type_user_id_key on public.account (provider, type, user_id);
create unique index account_provider_type_provider_account_id_key on public.account (provider, type, provider_account_id);
create index account_user_id_idx on public.account using btree (user_id);

create table public.session
(
    user_id     uuid          not null,
    session_id  varchar(1024) not null,
    logout_time timestamptz,
    ip_address  INET          not null,
    foreign key (user_id) references public.user (id) on update restrict on delete cascade,
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null,
    primary key (id)
) inherits (interfaces.resource)
  using heap;

create trigger update_timestamps
    before insert or update
    on public.session
    for each row
execute function public.ctutor_update_timestamps();

create index session_user_id_idx on public.profile using btree (user_id);

