create table if not exists public.course_group
(
    course_id           uuid not null references public.course (id) on delete cascade on update restrict,
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource,interfaces.title_description);

create unique index if not exists course_group_title_key on public.course_group (course_id, title);
create unique index if not exists course_group_course_id_key on public.course_group (course_id, id);

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_group
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();