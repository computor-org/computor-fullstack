create table public.course_content_kind
(
    primary key (id),
    has_ascendants          boolean     not null,
    has_descendants         boolean     not null,
    submittable             boolean     not null
) inherits (interfaces.string_id,interfaces.title_description);
insert into public.course_content_kind (id, title, description, has_ascendants, has_descendants, submittable)
values  ('assignment', 'Assignment', 'A task format where students submit their work for evaluation.', true, false, true),
        ('unit', 'Unit', 'A specialized organizational unit that serves as a directory for weekly or thematic content.', true, true, false),
        ('folder', 'Folder', 'A general directory for grouping content without thematic specialization.', true, true, false),
        ('quiz', 'Quiz', 'An interactive test where learners answer questions to assess their knowledge.', true, false, true);