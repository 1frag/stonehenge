drop table if exists app_google_users cascade;
drop table if exists app_vk_users cascade;
drop table if exists app_users cascade;
drop table if exists app_tests cascade;
drop table if exists app_marks cascade;
drop type if exists user_mission cascade;
drop type if exists auth_type cascade;

create table app_google_users (
    google_id decimal not null primary key
);

create table app_vk_users (
    vk_id decimal not null primary key
);

create type user_mission as enum ('student', 'teacher', 'advertiser');
create type auth_type as enum ('custom', 'google', 'vk');

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
    data bytea
);

create table app_marks (
    id serial primary key,
    solver int references app_users(id),
    point float4 not null,
    test int references app_tests(id)
);
