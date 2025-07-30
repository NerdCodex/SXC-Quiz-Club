CREATE DATABASE IF NOT EXISTS sxcquizclub;
USE sxcquizclub;


CREATE TABLE IF NOT EXISTS admins (
    aid INT PRIMARY KEY AUTO_INCREMENT,
    admin_name VARCHAR(200) NOT NULL,
    admin_email VARCHAR(200) NOT NULL,
    admin_password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    eid INT PRIMARY KEY AUTO_INCREMENT,
    event_name VARCHAR(200) NOT NULL,
    event_description TEXT,
    event_date DATE NOT NULL,
    event_starttime TIME NOT NULL,
    event_endtime TIME NOT NULL,
    event_banner BLOB NOT NULL
);


CREATE TABLE IF NOT EXISTS questions (
    qid INT PRIMARY KEY AUTO_INCREMENT,
    eid INT NOT NULL,
    question TEXT NOT NULL,
    image BLOB,
    FOREIGN KEY (eid) REFERENCES events(eid) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS question_options (
    option_id INT PRIMARY KEY AUTO_INCREMENT,
    qid INT NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (qid) REFERENCES questions(qid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    uid INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    regno VARCHAR(6),  -- NULL for teachers
    role ENUM('student', 'teacher') NOT NULL
);


CREATE TABLE IF NOT EXISTS results (
    rid INT PRIMARY KEY AUTO_INCREMENT,
    eid INT NOT NULL,
    uid INT NOT NULL,
    score INT NOT NULL,
    total_marks INT NOT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (eid) REFERENCES events(eid) ON DELETE CASCADE,
    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS answers (
    aid INT PRIMARY KEY AUTO_INCREMENT,
    rid INT NOT NULL,
    qid INT NOT NULL,
    selected_option_id INT,
    FOREIGN KEY (rid) REFERENCES results(rid) ON DELETE CASCADE,
    FOREIGN KEY (qid) REFERENCES questions(qid) ON DELETE CASCADE,
    FOREIGN KEY (selected_option_id) REFERENCES question_options(option_id) ON DELETE SET NULL
);
