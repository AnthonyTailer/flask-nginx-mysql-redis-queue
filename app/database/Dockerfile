# base image
FROM mysql:5.7

# set custom configs
ADD ./mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf
EXPOSE 3306 32000


# install requirements
RUN apt-get update
RUN apt-get install nano

CMD ["/usr/sbin/mysqld", "--skip-grant-tables", "--skip-networking", "--user=mysql"]
