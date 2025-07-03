create type public.organization_type as enum ('user', 'community', 'organization');
create cast (CHARACTER VARYING as public.organization_type) with inout as implicit;
create table if not exists public.organization
(
    organization_type public.organization_type not null,
    user_id           uuid                     null references public.user (id) on update restrict on delete cascade,
    path              ltree                    not null,
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource, interfaces.number, interfaces.title_description, interfaces.archivable,
            interfaces.contact,
            interfaces.address)
  using heap;

create unique index if not exists organization_number_key on public.organization (organization_type, number);
create unique index if not exists organization_path_key on public.organization (organization_type, path);
create unique index if not exists organization_user_key on public.organization (user_id) where user_id is not null;
create index if not exists organization_organization_type_idx on public.organization (organization_type);
create index if not exists organization_path_gist_idx on public.organization using GIST (path);
create index if not exists organization_path_idx on public.organization using BTREE (path);

alter table public.organization
    add constraint organization_user_condition check ( (organization_type = 'user' and user_id is not null) or
                                                       (organization_type <> 'user' and user_id is null) );

alter table public.organization
    add constraint organization_title_condition check ( (organization_type = 'user' and title is null) or
                                                        (organization_type <> 'user' and title is not null) );
alter table public.organization
    add column parent_path ltree generated always as ( case when nlevel("path") > 1
                                                                then subpath("path", 0, nlevel("path") - 1) end ) stored;
-- on update not working with generated columns
alter table public.organization
    add constraint fk_organization_parent foreign key (organization_type, parent_path) references public.organization (organization_type, path) on delete cascade deferrable initially deferred;

create or replace function public.organization_after_insert_or_update() returns trigger as
$$
begin
    if TG_OP = 'UPDATE' then
        if OLD.path is distinct from NEW.path then
            update public.organization
            set path = NEW.path || subpath(path, nlevel(OLD.path))
            where path <@ OLD.path
              and organization_type = new.organization_type
              and path != OLD.path;
        end if;
        if OLD.archived_at is distinct from NEW.archived_at then
            update public.organization
            set archived_at = NEW.archived_at
            where path <@ OLD.path
              and organization_type = NEW.organization_type;
        end if;
    end if;
    return new;
end;
$$ language plpgsql;

create trigger trigger_organization_after_insert_or_update
    after insert or update
    on public.organization
    for each row
execute function public.organization_after_insert_or_update();

create trigger update_timestamps
    before insert or update
    on public.organization
    for each row
execute function public.ctutor_update_timestamps();


create or replace function public.organization_before_insert_or_update() returns trigger as
$$
declare
    label TEXT;
    level INT;
begin
    if new.user_id is not null then NEW.path := NEW.user_id::text::ltree; end if;

    if new.path is not null then
        for level in 0..nlevel(NEW.path) - 1
            loop
                label := subpath(NEW.path, level, 1)::text;

                if length(label) > 63 then raise exception 'organization_valid_path'; end if;

                if not public.ctutor_valid_label(label) then raise exception 'organization_valid_path'; end if;
            end loop;
    end if;
    return new;
end;
$$ language plpgsql;


create trigger trigger_organization_before_insert_or_update
    before insert or update
    on public.organization
    for each row
execute function public.organization_before_insert_or_update();


-- create or replace function public.user_after_insert() returns trigger as
-- $$
-- begin
--     -- set search_path = "$user", public, extensions;
--     insert into public.organization (user_id, organization_type, path) values (NEW.id, 'user', '');
--     return NEW;
-- end;
-- $$ language plpgsql;

-- create trigger trigger_user_after_insert
--     after insert
--     on public.user
--     for each row
-- execute function public.user_after_insert();


-- create or replace function public.organization_prevent_deletion() returns TRIGGER as
-- $$
-- begin
--     if old.user_id is not null then
--         if exists ( select 1 from public.user where id = OLD.user_id ) then
--             raise exception 'organization_prevent_user_org_deletion';
--         end if;
--     end if;
--     return OLD;
-- end;
-- $$ language plpgsql;



-- create trigger trigger_organization_prevent_deletion
--     before delete
--     on public.organization
--     for each row
-- execute function public.organization_prevent_deletion();

