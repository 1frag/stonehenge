drop table if exists app_google_users cascade;
drop table if exists app_vk_users cascade;
drop table if exists app_users cascade;
drop table if exists app_tests cascade;
drop table if exists app_marks cascade;
drop table if exists app_levels cascade;
drop type if exists user_mission cascade;
drop type if exists auth_type cascade;
drop type if exists type_answer cascade;
drop extension if exists hstore;

create extension if not exists hstore;

create table app_google_users (
    google_id decimal not null primary key
);

create table app_vk_users (
    vk_id decimal not null primary key
);

create type user_mission as enum ('student', 'teacher', 'advertiser');
create type auth_type as enum ('custom', 'google', 'vk');
create type type_answer as enum ('pt', 'ch');

create table app_users (
    id serial primary key,
    login varchar(32) not null,
    first_name varchar(64) not null,
    last_name varchar(64) not null,
    email varchar(256) not null,
    mission user_mission not null,
    password varchar(256) null,
    google_id decimal references app_google_users(google_id),
    vk_id decimal references app_vk_users(vk_id),
    auth_type auth_type not null
);

create table app_tests (
    id serial primary key,
    author int references app_users(id),
    created_at timestamp default now(),
    type_answer type_answer not null,
    correct varchar(256),
    choice jsonb,
    question_txt varchar(1024),
    question_bytes bytea,
    case_ins bool null
);

create table app_marks (
    id serial primary key,
    solver int references app_users(id),
    point float4 not null,
    test int references app_tests(id)
);

create table app_levels (
    id serial primary key,
    name varchar(64) unique not null,
    description varchar(256),
    force int2 unique
);

create table app_tests_levels (
    id serial primary key,
    test_id int references app_tests(id),
    level_id int references app_levels(id),
    unique (test_id, level_id)
);

insert into app_levels (name, force)
values ('elementary', 1), ('A1', 2), ('A2', 3),
       ('B1', 4), ('B2', 5), ('C1', 6), ('C2', 7);
