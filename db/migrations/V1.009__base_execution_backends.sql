create table public.execution_backend
(
    type       varchar(255) not null,
    slug       varchar(255) not null,
    constraint check_slug check (slug ~* '^[A-Za-z0-9_-]+$'),
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource);

create unique index execution_backend_slug_key on public.execution_backend (slug);

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.execution_backend
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();