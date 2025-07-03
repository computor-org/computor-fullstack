create or replace function public.ctutor_valid_slug(label TEXT) returns BOOLEAN as
$$
begin
    return label ~ '^[a-z0-9]([-_a-z0-9]*[a-z0-9])?$';
end;
$$ language plpgsql;

create type public.ctutor_group_type as enum ('fixed','dynamic');


create table public.role
(
    primary key (id),
    builtin boolean not null default false,
    constraint builtin_id_must_start_with_underscore check (not builtin or id ~ '^_'),
    constraint id_label_valid check ( (builtin and public.ctutor_valid_slug(substring(id from 2))) or
                                      (not builtin and public.ctutor_valid_slug(id)) )
) inherits (interfaces.string_id, interfaces.title_description);

insert into public.role (id, builtin, title, description)
values ('_admin', true, 'Administrator', 'Full system permissions.'),
       ('_user_manager', true, 'User Manager', 'Manage user accounts and permissions.'),
       ('_organization_manager', true, 'Organization Manager', 'Manage organizations and their members.');

create trigger trigger_prevent_builtin_role_deletion
    before delete
    on public.role
    for each row
execute function public.ctutor_prevent_builtin_deletion();


create table public.user_role
(
    user_id    uuid references public.user (id) on delete cascade,
    role_id    varchar(50) references public.role (id) on delete restrict on update cascade,
    transient  boolean              default false,
    version    bigint               default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    created_by uuid,
    updated_by uuid,
    primary key (user_id, role_id)
);

create trigger update_timestamps
    before insert or update
    on public.user_role
    for each row
execute function public.ctutor_update_timestamps();

create table public.role_claim
(
    role_id     varchar(50) references public.role (id) on delete cascade,
    claim_type  varchar(255) not null,
    claim_value varchar(255) not null,
    version     bigint                default 0,
    created_at  timestamptz  not null default now(),
    updated_at  timestamptz  not null default now(),
    created_by  uuid,
    updated_by  uuid,
    properties  jsonb,
    primary key (role_id, claim_type, claim_value)
);

create trigger update_timestamps
    before insert or update
    on public.role_claim
    for each row
execute function public.ctutor_update_timestamps();

create table public.group
(
    primary key (id),
    type ctutor_group_type default 'fixed',
    constraint slug_valid check (public.ctutor_valid_slug(slug))
) inherits (interfaces.resource, interfaces.slugged);

create trigger update_timestamps
    before insert or update
    on public.group
    for each row
execute function public.ctutor_update_timestamps();

create table public.user_group
(
    user_id    uuid references public.user (id) on delete cascade,
    group_id   uuid references public.group (id) on delete restrict on update cascade,
    transient  boolean              default false,
    version    bigint               default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    created_by uuid,
    updated_by uuid,
    primary key (user_id, group_id)
);

create trigger update_timestamps
    before insert or update
    on public.user_group
    for each row
execute function public.ctutor_update_timestamps();

create table public.group_claim
(
    group_id    uuid references public.group (id) on delete cascade,
    claim_type  varchar(255) not null,
    claim_value varchar(255) not null,
    version     bigint                default 0,
    created_at  timestamptz  not null default now(),
    updated_at  timestamptz  not null default now(),
    created_by  uuid,
    updated_by  uuid,
    properties  jsonb,
    primary key (group_id, claim_type, claim_value)
);

create or replace function public.ctutor_check_fixed_group() returns TRIGGER as
$$
begin
    if not exists ( select 1 from public.group g where g.id = NEW.group_id and g.type = 'fixed' ) then
        raise exception 'group_not_fixed';
    end if;
    return NEW;
end;
$$ language plpgsql;

create trigger trg_check_fixed_group
    before insert or update
    on public.group_claim
    for each row
execute function public.ctutor_check_fixed_group();

create trigger update_timestamps
    before insert or update
    on public.group_claim
    for each row
execute function public.ctutor_update_timestamps();

create or replace function public.ctutor_prevent_group_type_change() returns TRIGGER as
$$
begin
    if OLD.type = 'fixed' and NEW.type = 'dynamic' then
        if exists ( select 1 from public.group_claim gc where gc.group_id = OLD.id ) then
            raise exception 'group_claim_references_fixed_group';
        end if;
    end if;
    return NEW;
end;
$$ language plpgsql;

create trigger trg_prevent_type_change
    before update
    on public.group
    for each row
execute function public.ctutor_prevent_group_type_change();

