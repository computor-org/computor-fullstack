create table public.course_execution_backend
(
    execution_backend_id    uuid not null references public.execution_backend (id) on update restrict on delete cascade,
    course_id               uuid not null references public.course (id) on update restrict on delete cascade,
    version                 bigint               default 0,
    created_at              timestamptz not null default now(),
    updated_at              timestamptz not null default now(),
    created_by              uuid,
    updated_by              uuid,
    properties              jsonb,
    primary key (course_id, execution_backend_id)
);

CREATE TRIGGER update_updated_at_trigger
BEFORE UPDATE ON public.course_execution_backend
FOR EACH ROW
EXECUTE FUNCTION public.ctutor_update_timestamps();