create table "media" (
    id uuid primary key,
    type varchar(16) not null,
    size_bytes bigint not null,
    extension varchar(16) not null,
    created_timestamp timestamp not null default now()
);

create table "user" (
    id uuid primary key,
    public_id varchar(32) not null unique,
    password varchar(64) not null,
    email varchar(64) not null,
    user_salt varchar(32) not null,
    first_name varchar(32) not null,
    last_name varchar(32),
    avatar_photo_id uuid references "media" ("id"),
    profile_status varchar(64),
    profile_bio varchar(512),
    created_timestamp timestamp not null default now()
);

create table "user_settings" (
    user_id uuid primary key references "user" ("id")
);

create table "user_contact" (
    user_id uuid not null references "user" ("id"),
    contact_user_id uuid not null references "user" ("id"),
    created_timestamp timestamp not null default now()
);

create table "session" (
    id uuid primary key,
    user_id uuid not null references "user" ("id"),
    ip varchar(15),
    user_agent varchar(64),
    is_active bool not null default true,
    device_fingerprint varchar(32),
    created_timestamp timestamp not null default now()
);

create table "geoip" (
    ip varchar(15) primary key,
    state varchar(64),
    country varchar(64),
    city varchar(64),
    updated_timestamp timestamp not null,
    created_timestamp timestamp not null default now()
);

create table "chat" (
    id uuid primary key,
    type varchar(16) not null,
    name varchar(32),
    avatar_photo_id uuid references "media" ("id"),
    description varchar(256),
    created_timestamp timestamp not null default now()
);

create sequence message_order_id_seq as bigint;

create table "message" (
    id uuid primary key,
    type varchar(16) not null,
    chat_id uuid not null references "chat" ("id"),
    sender_user_id uuid references "user" ("id"),
    sender_chat_id uuid references "chat" ("id"),
    message_text varchar(4096),
    audio_msg_file_id uuid references "media" ("id"),
    video_msg_file_id uuid references "media" ("id"),
    reply_to_message uuid references "message" ("id"),
    forwarded_message uuid references "message" ("id"),
    is_silent bool not null default false,
    last_edited_at timestamp,
    created_timestamp timestamp not null default now(),
    order_id bigint not null default nextval('message_order_id_seq'::regclass)
);

create index idx_message_order_id on "message" ("order_id");

create table "chat_user" (
    chat_id uuid references "chat" ("id"),
    user_id uuid references "user" ("id"),
    is_chat_owner bool not null default false,
    last_available_message uuid references "message" ("id"),
    created_timestamp timestamp not null default now(),
    primary key ("chat_id", "user_id")
);

create table "message_read" (
    message_id uuid references "message" ("id"),
    user_id uuid references "user" ("id"),
    created_timestamp timestamp not null default now(),
    primary key ("message_id", "user_id")
);

create table "message_attachment" (
    message_id uuid references "message" ("id"),
    media_id uuid references "media" ("id"),
    primary key ("message_id", "media_id")
);

create sequence update_order_id_seq as bigint;

create table "update" (
    id uuid primary key,
    type varchar(16) not null,
    user_id uuid not null references "user" ("id"),
    update_message_id uuid references "message" ("id"),
    order_id bigint not null default nextval('update_order_id_seq'::regclass)
);

create index idx_update_order_id on "update" ("order_id");

