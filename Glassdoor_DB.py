import mysql.connector


def main():
    """Creating the glassdoor database and tables"""

    # Creating the Glassdoor database
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="password")

    # creating a cursor
    my_cursor = mydb.cursor()

    my_cursor.execute("CREATE DATABASE glassdoor_db")

    # Connecting to our created database and creating the tables

    # Connecting to the database -
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="password",
        database="glassdoor_db")

    # creating a cursor
    my_cursor = mydb.cursor()

    # Creating the locations table
    my_cursor.execute("""CREATE TABLE locations (
                      location VARCHAR(100),
                      country VARCHAR(100),
                      city VARCHAR(100),
                      longitude FLOAT,
                      latitude FLOAT,
                      PRIMARY KEY(country, city)

  )
  """)

    # Creating the companies table
    my_cursor.execute("""CREATE TABLE companies (
                      company_name VARCHAR(100),
                      country VARCHAR(100),
                      city VARCHAR(100),
                      FOREIGN KEY(country, city) REFERENCES locations(country, city),
                      size VARCHAR(100),
                      founded INTEGER,
                      type VARCHAR(100),
                      industry VARCHAR(100),
                      sector VARCHAR(100),
                      revenue VARCHAR(100),
                      rating FLOAT,
                      PRIMARY KEY(company_name)
  )
  """)

    # Creating the jobs_reqs table
    my_cursor.execute("""CREATE TABLE job_reqs (
                      job_id BIGINT,
                      title VARCHAR(100),
                      description TEXT,
                      company VARCHAR(100),
                      FOREIGN KEY(company) REFERENCES companies(company_name),
                      scrape_date DATETIME,
                      location VARCHAR(100),
                      country VARCHAR(100),
                      city VARCHAR(100),
                      FOREIGN KEY(country, city) REFERENCES locations(country, city),
                      PRIMARY KEY(job_id)
  )
  """)


if __name__ == "__main__":
    main()
