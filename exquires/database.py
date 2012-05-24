#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of
#  EXQUIRES | Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
#

"""Provides an interface to the sqlite3 image error database."""

import sqlite3


class Database:

    """This class provides an interface to the sqlite3 image error database.

    The database is used to store error data computed by :mod:`compute_error`.
    """

    def __init__(self, dbasefile):
        """This constructor creates a new Database object.

        :param dbasefile: The database file to connect to.

        """
        self.dbase = sqlite3.connect(dbasefile,
                                     detect_types=sqlite3.PARSE_DECLTYPES)
        self.dbase.row_factory = sqlite3.Row
        self.dbase.text_factory = str
        self.sql_do('CREATE TABLE IF NOT EXISTS TABLEDATA (name TEXT PRIMARY'
                    ' KEY, image TEXT, downsampler TEXT, ratio TEXT )')

    def sql_do(self, sql, params=()):
        """Perform an operation on the database and commit the changes.

        :param sql: The SQL statement to execute and commit.
        :param params: Values to fill any wildcards in the SQL statement.

        """
        self.dbase.execute(sql, params)
        self.dbase.commit()

    def __create_table(self, name, metrics):
        """Private method used to create a new database table.

        :param name: The name of the table to create.
        :param metric: The error metrics to compute (the table columns).

        """
        sql = 'CREATE TABLE {} ( upsampler TEXT PRIMARY KEY'.format(name)
        for metric in metrics:
            sql += ', {} DOUBLE'.format(metric)
        sql += ' )'
        self.sql_do(sql)

    def add_table(self, image, downsampler, ratio, metrics):
        """Add a new table to the database.

        Each table is defined in the following way:
            1. image, downsampler, and ratio define the table name
            2. metrics define the columns of the table

        To keep track of each table in terms of the image, downsampler, and
        ratio that defines it, an entry is created in the TABLEDATA table.

        :param image: The name of the image.
        :param downsampler: The name of the downsampler.
        :param ratio: The ratio in string form.
        :param metrics: The list of metric names.
        :return: The table name.

        """
        #create table
        name = '_'.join([image, downsampler, ratio])
        self.__create_table(name, metrics)

        #add table details to master table
        row = dict(name=name, image=image,
                   downsampler=downsampler, ratio=ratio)
        self.insert('TABLEDATA', row)
        self.dbase.commit()
        return name

    def backup_table(self, name, backup_name, metrics):
        """Backup an existing image error table.

        :param name: The name of the table to backup.
        :param backup_name: The name to use for the backup table.
        :param metrics: The error metrics (columns) to backup.

        """
        self.sql_do('ALTER TABLE {} RENAME TO {}'.format(name, backup_name))
        self.__create_table(name, metrics)

    def drop_backup(self, name):
        """Drop a backup table once it is no longer needed.

        :param name: The name of the backup table to drop.

        """
        self.sql_do('DROP TABLE {}'.format(name))

    def drop_tables(self, images, downsamplers, ratios):
        """Drop database tables.

        All tables defined by any of the images, downsamplers, or ratios are
        dropped. The TABLEDATA table is updated to reflect these changes.

        :param images: The list of image names.
        :param downsamplers: The list of downsampler names.
        :param ratios: The list of ratios in string form.

        """
        if len(images) or len(downsamplers) or len(ratios):
            query = 'SELECT name FROM TABLEDATA WHERE'
            for image in images:
                query = query + ' image = \'{}\' OR'.format(image)
            for downsampler in downsamplers:
                query = query + ' downsampler = \'{}\' OR'.format(downsampler)
            for ratio in ratios:
                query = query + ' ratio = \'{}\' OR'.format(ratio)
            query = query.rstrip(' OR')
            cursor = self.dbase.cursor()
            cursor.execute(query)
            names = [(table[0],) for table in cursor.fetchall()]

            # Delete the rows from TABLEDATA and drop the tables by name.
            self.dbase.executemany('DELETE FROM TABLEDATA WHERE name = ?',
                                   names)
            for name in names:
                self.dbase.execute(' '.join(['DROP TABLE', name[0]]))
            self.dbase.commit()

    def sql_fetchall(self, sql, params=()):
        """Fetch all rows for the specified SQL query.

        :param sql: The SQL operation string to execute.
        :param params: The parameter list.
        """
        cursor = self.dbase.execute(sql, params)
        return cursor.fetchall()

    def get_error_data(self, table, upsampler, metrics_str):
        """Return a filtered row of error data.

        For the upsampler row in the table, return a dictionary containing only
        the error data for the specified metrics.

        :param table: The name of the table to query.
        :param upsampler: The name of the upsampler (row) to acquire data from.
        :param metrics_str: A comma-separated string of the metrics to
                            return error data for.

        """
        sql = 'SELECT {} FROM {} WHERE upsampler=\'{}\''
        query = sql.format(metrics_str, table, upsampler)
        cursor = self.dbase.execute(query)
        return dict(cursor.fetchone())

    def insert(self, table, row):
        """Insert a single row into the table, or update if it exists.

        :param table: The name of the table.
        :param row: A dictionary of key/value pairs that define the row.

        """
        keys = sorted(row.keys())
        values = [row[v] for v in keys]
        query = 'INSERT OR REPLACE INTO {} ({}) VALUES ({})'.format(
            table, ', '.join(keys), ', '.join('?' for i in range(len(values))))
        self.dbase.execute(query, values)
        self.dbase.commit()

    def delete(self, table, upsampler):
        """Delete a row from the table.

        :param table: The name of the table to delete from.
        :param upsampler: The upsampler row to remove from the table.

        """
        query = 'DELETE FROM {} where upsampler = ?'.format(table)
        self.dbase.execute(query, [upsampler])
        self.dbase.commit()

    def close(self):
        """Close the connection to the database."""
        self.dbase.close()
