CREATE TABLE course_submission_group_member
(
    grading                     float,
    course_id                   uuid          not null references public.course (id) on update restrict on delete restrict,
    course_submission_group_id  uuid          not null references public.course_submission_group (id) on update restrict on delete cascade,
    course_member_id            uuid          not null references public.course_member (id) on update restrict on delete restrict,
    course_content_id           uuid          not null references public.course_content (id) on update restrict on delete restrict,
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource);

create unique index course_submission_group_member_key on public.course_submission_group_member (course_submission_group_id, course_member_id);
create unique index course_submission_group_course_content_key on public.course_submission_group_member (course_member_id, course_content_id);

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_submission_group_member
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();

CREATE OR REPLACE FUNCTION set_course_content_id_from_course_submission_group()
RETURNS TRIGGER AS $$
BEGIN
    NEW.course_content_id := (SELECT course_content_id FROM public.course_submission_group WHERE id = NEW.course_submission_group_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_course_content_id_course_submission_group_id
BEFORE INSERT OR UPDATE ON public.course_submission_group_member
FOR EACH ROW
EXECUTE FUNCTION set_course_content_id_from_course_submission_group();

CREATE OR REPLACE FUNCTION set_course_id_from_course_member()
RETURNS TRIGGER AS $$
BEGIN
    NEW.course_id := (SELECT course_id FROM public.course_member WHERE id = NEW.course_member_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_course_id_course_member_id
BEFORE INSERT OR UPDATE ON public.course_submission_group_member
FOR EACH ROW
EXECUTE FUNCTION set_course_id_from_course_member();