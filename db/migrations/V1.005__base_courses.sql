create table if not exists public.course
(
    path                    ltree           not null,
    course_family_id        uuid            not null references public.course_family (id) on delete cascade on update restrict,
    organization_id         uuid            not null references public.organization (id) on delete cascade on update restrict,
    version_identifier      varchar(2048),
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource,interfaces.title_description);

create unique index if not exists course_path_key on public.course (course_family_id, path);
create index if not exists course_path_idx on public.course using BTREE (path);

CREATE OR REPLACE FUNCTION set_organization_id_from_course_family()
RETURNS TRIGGER AS $$
BEGIN
    NEW.organization_id := (SELECT organization_id FROM public.course_family WHERE id = NEW.course_family_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_organization_id_course_family_id
BEFORE INSERT ON public.course
FOR EACH ROW
EXECUTE FUNCTION set_organization_id_from_course_family();

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();