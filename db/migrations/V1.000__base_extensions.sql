create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;
create extension if not exists ltree;
create extension if not exists citext;

create type public.ctutor_color as enum ('red', 'orange','amber', 'yellow','lime','green','emerald','teal','cyan','sky','blue','indigo','violet', 'purple','fuchsia','pink','rose');


create or replace function public.ctutor_valid_label(label TEXT) returns BOOLEAN as
$$
begin
    return label ~ '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$';
end;
$$ language plpgsql;

create or replace function public.ctutor_update_timestamps() returns TRIGGER as
$$
begin
    if TG_OP = 'INSERT' then
        NEW.created_at := now();
        NEW.updated_at := now();
    elsif TG_OP = 'UPDATE' then
        new.created_at := old.created_at;
        NEW.updated_at := now();
    end if;
    return NEW;
end;
$$ language plpgsql;

create or replace function ctutor_prevent_builtin_deletion() returns TRIGGER as
$$
begin
    if OLD.builtin then raise exception 'Cannot delete a built-in: %', OLD.name; end if;
    return OLD;
end;
$$ language plpgsql;