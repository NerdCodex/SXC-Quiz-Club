CREATE SCHEMA IF NOT EXISTS SXC;
USE SXC;

CREATE TABLE IF NOT EXISTS admins (
    aid INT PRIMARY KEY AUTO_INCREMENT,
    admin_name VARCHAR(200) NOT NULL UNIQUE,
    admin_email VARCHAR(200) NOT NULL UNIQUE,
    admin_password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS EVENTS(
    eid int primary key auto_increment,
    event_name text not null,
    event_description text not null,
    event_date date not null,
    event_starttime time not null,
    event_endtime time not null,
    event_banner longblob,
    slugurl VARCHAR(255) UNIQUE
);

CREATE TABLE IF NOT EXISTS questions (
    qid INT PRIMARY KEY AUTO_INCREMENT,
    eid INT,
    question TEXT NOT NULL,
    option_a VARCHAR(255),
    option_b VARCHAR(255),
    option_c VARCHAR(255),
    option_d VARCHAR(255),
    correct_answer CHAR(1) NOT NULL,
    image_path TEXT,
    score INT NOT NULL DEFAULT 1,
    FOREIGN KEY (eid) REFERENCES events(eid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS responses (
    rid INT PRIMARY KEY AUTO_INCREMENT,
    eid INT,
    name_ TEXT NOT NULL,
    email varchar(255) NOT NULL,
    regno TEXT,
    percentage_secured FLOAT NOT NULL,
    FOREIGN KEY (eid) REFERENCES events(eid) ON DELETE CASCADE,
    UNIQUE (eid, email)
);

CREATE TABLE IF NOT EXISTS certificates (
    cid INT PRIMARY KEY AUTO_INCREMENT,
    eid INT,
    email TEXT NOT NULL,
    certificate_url TEXT NOT NULL,
    FOREIGN KEY (eid) REFERENCES events(eid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gallery(
	gid INT PRIMARY KEY AUTO_INCREMENT,
    image LONGBLOB,
    image_desc TEXT NOT NULL
);
