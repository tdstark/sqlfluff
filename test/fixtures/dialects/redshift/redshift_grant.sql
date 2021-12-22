GRANT INSERT ON TABLE factdata.table_one TO test_user;
GRANT INSERT ON factdata.table_one TO test_user;
GRANT UPDATE ON TABLE factdata.table_one, factdata.table_two TO test_user;
GRANT DELETE ON TABLE factdata.table_one TO test_user, GROUP test_users;
GRANT DROP ON TABLE table_one TO GROUP test_users;
GRANT REFERENCES ON TABLE table_one TO PUBLIC;

GRANT SELECT ON ALL TABLES IN SCHEMA factdata TO test_user, test_user2;
GRANT SELECT ON ALL TABLES IN SCHEMA factdata TO test_user WITH GRANT OPTION;
GRANT SELECT ON ALL TABLES IN SCHEMA factdata TO GROUP test_users;
GRANT USAGE ON SCHEMA factdata TO GROUP test_users;
ALTER DEFAULT PRIVILEGES IN SCHEMA factdata GRANT SELECT ON TABLES TO GROUP test_users;

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA factdata TO test_user;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA factdata TO test_user;
GRANT EXECUTE ON FUNCTION test_function() TO test_user;

GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA factdata TO test_user;
GRANT ALL ON ALL PROCEDURES IN SCHEMA factdata TO test_user;
GRANT EXECUTE ON PROCEDURE test_procedure() TO test_user;
GRANT EXECUTE ON PROCEDURE test_procedure1(), test_procedure2() TO test_user;

GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;
GRANT CREATE ON DATABASE test_db TO test_user;
GRANT TEMPORARY ON DATABASE test_db TO test_user WITH GRANT OPTION;
GRANT TEMPORARY ON DATABASE test_db TO GROUP test_user;
GRANT TEMP ON DATABASE test_db TO PUBLIC;

GRANT USAGE ON LANGUAGE sql TO test_user;
GRANT USAGE ON LANGUAGE plpythonu TO test_user;
GRANT USAGE ON LANGUAGE plpythonu, sql TO GROUP test_users;
