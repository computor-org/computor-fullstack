create table if not exists public.course_role
(
    primary key (id)
) inherits (interfaces.string_id,interfaces.title_description);
insert into public.course_role (id, title, description)
values ('_owner', 'Owner', 'An owner role with full permissions.'),
       ('_maintainer', 'Maintainer', 'A maintainer role with high-level access permissions.'),
       ('_study_assistant', 'Study Assistant', 'A study assistant role with appropriate access permissions.'),
       ('_student', 'Student', 'A student role with standard access permissions.');

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_role
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();