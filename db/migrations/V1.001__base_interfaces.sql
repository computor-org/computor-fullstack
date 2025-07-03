create schema if not exists interfaces;

create table interfaces.string_id
(
    id varchar(255)
) using heap;

create table interfaces.resource
(
    id         uuid        not null default uuid_generate_v4(),
    version    bigint               default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    created_by uuid,
    updated_by uuid,
    properties jsonb
) using heap;

create table interfaces.archivable
(
    archived_at timestamptz default null
) using heap;

create table interfaces.title_description
(
    title       varchar(255),
    description varchar(4096)
) using heap;

create table interfaces.slugged
(
    slug varchar(255) not null
) inherits (interfaces.title_description)
  using heap;

create table interfaces.number
(
    number varchar(255)
) using heap;

create table interfaces.contact
(
    email      varchar(320),
    telephone  varchar(255),
    fax_number varchar(255),
    url        varchar(2048)
) using heap;

create table interfaces.avatar
(
    avatar_color integer,
    avatar_image varchar(2048)
) using heap;

create table interfaces.address
(
    postal_code    varchar(255),
    street_address varchar(1024),
    locality       varchar(255),
    region         varchar(255),
    country        varchar(255)
) using heap;

