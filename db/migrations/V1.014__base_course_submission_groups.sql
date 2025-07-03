create table public.course_submission_group
(
    status                      varchar(2048),
    grading                     float,
    max_group_size              int             not null    default 1,
    max_test_runs               int,
    max_submissions             int,
    course_id                   uuid            not null references public.course (id) on update restrict on delete cascade,
    course_content_id           uuid            not null references public.course_content (id) on update restrict on delete cascade,
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource);

CREATE OR REPLACE FUNCTION set_course_id_from_course_content()
RETURNS TRIGGER AS $$
BEGIN
    NEW.course_id := (SELECT course_id FROM public.course_content WHERE id = NEW.course_content_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_course_content_submittable()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM public.course_content cc
        JOIN public.course_content_type cct ON cc.course_content_type_id = cct.id
        JOIN public.course_content_kind cck ON cct.course_content_kind_id = cck.id
        WHERE cc.id = NEW.course_content_id
        AND cck.submittable = TRUE
    ) THEN
        RAISE EXCEPTION 'course_content_id must be of a submittable course_content_kind_id';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_course_content_submittable
BEFORE INSERT OR UPDATE ON public.course_submission_group
FOR EACH ROW EXECUTE FUNCTION check_course_content_submittable();

CREATE TRIGGER trg_set_course_id_course_content_id
BEFORE INSERT ON public.course_submission_group
FOR EACH ROW
EXECUTE FUNCTION set_course_id_from_course_content();

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_submission_group
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();