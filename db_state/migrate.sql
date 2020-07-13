create table app_levels (
    id serial primary key,
    name varchar(64) unique not null,
    description varchar(256),
    force int2 unique
);

create table app_google_users (
    google_id decimal not null primary key
);

create table app_vk_users (
    vk_id decimal not null primary key
);

create type user_mission as enum ('student', 'teacher', 'advertiser');
create type auth_type as enum ('custom', 'google', 'vk');
create type type_answer as enum ('pt', 'ch');

create table app_student_meta (
    id serial primary key,
    level_id int references app_levels(id) on delete set null
);

create table app_users (
    id serial primary key,
    login varchar(32) not null,
    first_name varchar(64) not null,
    last_name varchar(64) not null,
    email varchar(256) not null,
    mission user_mission not null,
    password varchar(256) null,
    google_id decimal references app_google_users(google_id) on delete set null,
    vk_id decimal references app_vk_users(vk_id) on delete set null,
    auth_type auth_type not null,
    student_meta_id int references app_student_meta(id) on delete set null
);

create table app_tests (
    id serial primary key,
    author int references app_users(id) on delete set null,
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
    solver int references app_users(id) on delete cascade,
    point float4 not null,
    test int references app_tests(id) on delete cascade,
    answer text,
    unique (solver, test)
);

create table app_tests_levels (
    id serial primary key,
    test_id int references app_tests(id) on delete cascade,
    level_id int references app_levels(id) on delete set null,
    unique (test_id, level_id)
);

insert into app_levels (name, force)
values ('beginner', 1), ('elementary', 2), ('pre-intermediate', 3),
       ('intermediate', 4), ('upper intermediate', 5),
       ('advanced', 6), ('mastery', 7);

create or replace function
    test_suitable_for_student(student int,
                              test int) returns bool as
$$
declare
    student_level int;
    result        bool;
begin
    select asm.level_id
    from app_users
    join app_student_meta asm on app_users.student_meta_id = asm.id
    into student_level;

    select count(*) <> 0
    into result
    from app_tests_levels r
    where r.test_id = test
      and r.level_id = student;

    return result;
end;
$$ language plpgsql;

create or replace function create_new_user(
    cur_login varchar(32),
    cur_email varchar(256),
    cur_first_name varchar(64),
    cur_last_name varchar(64),
    cur_mission user_mission,
    cur_password varchar(256),
    google_user decimal,
    vk_user decimal
) returns int as
$$
declare
    cur_auth_type auth_type = null;
    student_meta int = null;
    result int;
begin
    if google_user is not null then
        insert into app_google_users (google_id)
        values (google_user);
        cur_auth_type = 'google'::auth_type;
    elsif vk_user is not null then
        insert into app_vk_users (vk_id)
        values (vk_user);
        cur_auth_type = 'vk'::auth_type;
    else
        raise notice 'Unsupported non-oauth registration';
    end if;

    if cur_mission = 'student'::user_mission then
        insert into app_student_meta
        default values returning id into student_meta;
    end if;

    insert into app_users (login, first_name, last_name,
                           email, google_id, vk_id, mission,
                           auth_type, password, student_meta_id)
    values (cur_login, cur_first_name, cur_last_name,
            cur_email, google_user, vk_user, cur_mission,
            cur_auth_type, cur_password, student_meta)
    returning id into result;

    return result;
end;
$$ language plpgsql;

create or replace function get_next_test(
    student int
) returns int as
$$
declare
    student_level int;
    result int;
begin
    select asm.level_id into student_level from app_users au
    join app_student_meta asm on au.student_meta_id = asm.id
    where au.student_meta_id = asm.id and au.id = student;

    if student_level is null then
        raise 'UserMustSetLevel';
    end if;

    select t.id into result from app_tests t
    where t.id not in (
        select test from app_marks m
        where m.solver = student
    ) and test_suitable_for_student(student, t.id)
    order by t.id limit 1;

    return result;
end;
$$ language plpgsql;

create table app_video (
    id serial primary key,
    cloud_path text not null, -- disk:/stonehenge/...
    cloud_href text not null, -- https://cloud.../...
    title varchar(128) not null,
    description text,
    author int references app_users(id) on delete set null,
    created_at date default now()::date
);

create table app_views (
    id serial primary key,
    student int references app_users(id) on delete set null,
    video_id int references app_video(id) on delete cascade,
    how_many int default 0 not null
);

create table app_video_levels (
    id serial primary key,
    video_id int references app_video(id) on delete cascade,
    level_id int references app_levels(id) on delete set null,
    unique (video_id, level_id)
);
