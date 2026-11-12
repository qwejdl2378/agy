CREATE TABLE "user" (id serial PRIMARY KEY, email varchar(255) UNIQUE NOT NULL, password_hash varchar(255) NOT NULL, is_admin boolean DEFAULT false);
CREATE TABLE project (id serial PRIMARY KEY, name varchar(200) NOT NULL, slug varchar(200) UNIQUE NOT NULL, owner_id int REFERENCES "user"(id), created_at timestamp);
CREATE TABLE document (id serial PRIMARY KEY, project_id int REFERENCES project(id), title varchar(300), body text, file_path varchar(500));
CREATE INDEX ON document(project_id);
