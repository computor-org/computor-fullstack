create table public.course_content
(
    path                        ltree                       not null,
    course_id                   uuid                        not null    references public.course (id) on update restrict on delete cascade,
    course_content_type_id      uuid                        not null    references public.course_content_type (id) on update restrict on delete restrict,
    foreign key (course_id, course_content_type_id)                     references public.course_content_type (course_id, id) on update restrict on delete restrict,
    version_identifier          varchar(2048)               not null,
    position                    float                       not null,
    max_group_size              int,
    max_test_runs               int,
    max_submissions             int,
    execution_backend_id        uuid                        references public.execution_backend (id) on update restrict on delete cascade,
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource,interfaces.archivable,interfaces.title_description);

create unique index course_content_path_key on public.course_content (course_id, path);
create index if not exists course_content_path_idx on public.course_content using BTREE (path);

CREATE OR REPLACE FUNCTION check_course_content_max_group_size()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM public.course_content_type cct
        JOIN public.course_content_kind cck ON cct.course_content_kind_id = cck.id
        WHERE cct.id = NEW.course_content_type_id
        AND cck.submittable = TRUE
    ) THEN
        IF NEW.max_group_size IS NULL OR NEW.max_group_size < 1 THEN
            NEW.max_group_size := 1;
        END IF;
    ELSE
        NEW.max_group_size := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_course_content_max_group_size
BEFORE INSERT OR UPDATE ON public.course_content
FOR EACH ROW EXECUTE FUNCTION check_course_content_max_group_size();

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_content
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();