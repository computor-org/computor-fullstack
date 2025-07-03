create index idx_course_path_btree on public.course (path);
create index idx_course_family_path_btree on public.course_family (path);
create index idx_course_content_path_btree on public.course_content (path);

create index idx_course_path_gist on public.course using GIST (path);
create index idx_course_family_path_gist on public.course_family using GIST (path);
create index idx_course_content_path_gist on public.course_content using GIST (path);


create index idx_course_organization_id on public.course (organization_id);
create index idx_course_course_family_id on public.course (course_family_id);

create index idx_course_member_course_id on public.course_member (course_id);
create index idx_course_member_course_group_id on public.course_member (course_group_id);

create index idx_course_content_course_id on public.course_content (course_id);

create index idx_course_course_submission_group_member_course_id on public.course_submission_group_member (course_id);
create index idx_course_course_submission_group_member_course_content_id on public.course_submission_group_member (course_content_id);
create index idx_course_course_submission_group_member_course_member_id on public.course_submission_group_member (course_member_id);

create index idx_course_submission_group_course_id on public.course_submission_group (course_id);
create index idx_course_submission_group_course_content_id on public.course_submission_group (course_content_id);

create index idx_result_course_submission_group_id on public.result (course_submission_group_id);
create index idx_result_course_member_id on public.result (course_member_id);
create index idx_result_course_content_id on public.result (course_content_id);

create type public.codeability_message_type as enum ('note','message');

create table public.codeability_message
(
    primary key (id),
    type              public.codeability_message_type not null,
    sender            uuid                            not null references public.user (id) on delete cascade on update restrict,
    course_id         uuid                            null references public.course (id) on delete cascade on update restrict,
    course_group_id   uuid                            null references public.course_group (id) on delete cascade on update restrict,
    course_member_id  uuid                            null references public.course_member (id) on delete cascade on update restrict,
    course_content_id uuid                            null references public.course_content (id) on delete cascade on update restrict,
    message           varchar(4096)                   not null,
    foreign key (created_by) references public.user (id) on delete set null,
    foreign key (updated_by) references public.user (id) on delete set null
) inherits (interfaces.resource);

create index idx_message_course_id on public.codeability_message (course_id);
create index idx_message_course_group_id on public.codeability_message (course_group_id);
create index idx_message_course_member_id on public.codeability_message (course_member_id);
create index idx_message_course_content_id on public.codeability_message (course_content_id);

create table public.codeability_message_read
(
    message_id uuid not null references public.codeability_message (id) on delete cascade,
    user_id    uuid null references public.user (id) on update restrict on delete cascade,
    read_at    timestamp with time zone default now(),
    primary key (message_id, user_id)
);

create index idx_message_reads_user_id on public.codeability_message_read (user_id);
create index idx_message_reads_message_id on public.codeability_message_read (message_id);