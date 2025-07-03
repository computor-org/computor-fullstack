create table public.result
(
    submit                          boolean      not null,
    course_member_id                uuid         not null references public.course_member (id) on update restrict on delete cascade,
    course_submission_group_id      uuid         references public.course_submission_group (id) on update restrict on delete set null,
    course_content_id               uuid         not null references public.course_content (id) on update restrict on delete cascade,
    course_content_type_id          uuid         not null references public.course_content_type (id) on update restrict on delete restrict,
    execution_backend_id            uuid         not null references public.execution_backend (id) on update restrict on delete restrict,
    test_system_id                  varchar(255) not null,
    result                          float        not null,
    result_json                     jsonb,
    version_identifier              varchar(2048) not null,
    status                          int           not null,
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource);

create unique index result_version_identifier_member_key on public.result (course_member_id, course_content_id,version_identifier);
create unique index result_version_identifier_group_key on public.result (course_submission_group_id, course_content_id, version_identifier) where course_submission_group_id is not null;
create unique index result_commit_test_system_key on public.result (test_system_id, execution_backend_id);

CREATE TRIGGER trg_check_course_content_submittable
BEFORE INSERT OR UPDATE ON public.result
FOR EACH ROW EXECUTE FUNCTION check_course_content_submittable();

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.result
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();

CREATE OR REPLACE FUNCTION set_course_content_type_id_from_course_content()
RETURNS TRIGGER AS $$
BEGIN
    NEW.course_content_type_id := (SELECT course_content_type_id FROM public.course_content WHERE id = NEW.course_content_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_course_content_type_id_course_content_id
BEFORE INSERT OR UPDATE ON public.result
FOR EACH ROW
EXECUTE FUNCTION set_course_content_type_id_from_course_content();