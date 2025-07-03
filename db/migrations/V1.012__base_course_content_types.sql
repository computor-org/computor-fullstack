
create table public.course_content_type
(
    color                               public.ctutor_color                            null        default null,
    course_content_kind_id              varchar(255)                    not null references public.course_content_kind (id) on update restrict on delete cascade,
    course_id                           uuid                            not null references public.course (id) on update restrict on delete cascade,
    constraint check_slug check (slug ~* '^[A-Za-z0-9_-]+$'),
    primary key (id),
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource,interfaces.slugged);

create unique index course_content_type_slug_key on public.course_content_type (slug, course_id, course_content_kind_id);
create unique index course_content_type_course_id_key on public.course_content_type (id, course_id);

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_content_type
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();