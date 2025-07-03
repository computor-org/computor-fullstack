create table public.course_member
(
    user_id                 uuid    not null references public.user (id) on update restrict on delete cascade,
    course_id               uuid    not null references public.course (id) on update restrict on delete cascade,
    course_group_id         uuid    null references public.course_group (id) on update restrict on delete restrict,
    course_role_id          varchar not null references public.course_role (id) on update restrict on delete cascade,
    foreign key (course_id, course_group_id) references public.course_group (course_id, id) on update restrict on delete restrict,
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null,
    CONSTRAINT course_member_student_valid CHECK (
        CASE 
            WHEN course_role_id = '_student' THEN course_group_id IS NOT NULL
            ELSE TRUE
        END
    )
) inherits (interfaces.resource);
create unique index course_member_key on public.course_member (user_id, course_id);


CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_member
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();