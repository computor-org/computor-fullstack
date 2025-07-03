create table if not exists public.course_family
(
    path                        ltree           not null,
    organization_id             uuid            not null references public.organization (id) on delete cascade on update restrict,
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource,interfaces.title_description);

create unique index if not exists course_family_path_key on public.course_family (organization_id, path);
create index if not exists course_family_path_idx on public.course_family using BTREE (path);

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_family
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();