#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of the
#  EXQUIRES (EXtensible QUantitative Image RESampling) test suite
#

"""Provides an interface to the sqlite3 image error database."""

import sqlite3


class Database:

    """This class provides an interface to the sqlite3 image error database.

    The database stores error data computed by :ref:`exquires-run` and
    :ref:`exquires-update`. This data is retrieved and used to compute the
    output given by :ref:`exquires-report` and :ref:`exquires-correlate`.

    :param dbasefile: database file to connect to
    :type dbasefile:  `path`

    """

    def __init__(self, dbasefile):
        """Create a new :class:`Database` object."""
        self.dbase = sqlite3.connect(dbasefile,
                                     detect_types=sqlite3.PARSE_DECLTYPES)
        self.dbase.row_factory = sqlite3.Row
        self.dbase.text_factory = str
        self.sql_do('CREATE TABLE IF NOT EXISTS TABLEDATA (name TEXT PRIMARY'
                    ' KEY, image TEXT, downsampler TEXT, ratio TEXT )')

    def sql_do(self, sql, params=()):
        """Perform an operation on the database and commit the changes.

        :param sql:    SQL statement to execute and commit
        :param params: values to fill wildcards in the SQL statement
        :type sql:     `string`
        :type params:  `list of values`

        """
        self.dbase.execute(sql, params)
        self.dbase.commit()

    def __create_table(self, name, metrics):
        """Private method used to create a new database table.

        .. note::

            This is a private method called by :meth:`add_table` and
            :meth:`backup_table`.

        :param name:    name of the table to create
        :param metrics: error metrics to compute (the table columns)
        :type name:     `string`
        :type metrics:  `list of strings`

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

        :param image:       name of the image
        :param downsampler: name of the downsampler
        :param ratio:       resampling ratio
        :param metrics:     names of the metrics
        :type image:        `string`
        :type downsampler:  `string`
        :type ratio:        `string`
        :type metrics:      `list of strings`

        :return:            the table name
        :rtype:             `string`

        """
        # Create table.
        name = '_'.join([image, downsampler, ratio])
        self.__create_table(name, metrics)

        # Add table details to master table (TABLEDATA).
        row = dict(name=name, image=image,
                   downsampler=downsampler, ratio=ratio)
        self.insert('TABLEDATA', row)
        self.dbase.commit()
        return name

    def backup_table(self, name, metrics):
        """Backup an existing image error table.

        :param name:    name of the table to backup
        :param metrics: error metrics (columns) to backup
        :type name:     `string`
        :type metrics:  `list of strings`

        :return:        name of the backup table
        :rtype:         `string`

        """
        backup_name = '_'.join([name, 'bak'])
        self.sql_do('ALTER TABLE {} RENAME TO {}'.format(name, backup_name))
        self.__create_table(name, metrics)
        return backup_name

    def get_tables(self, args):
        """Return table names for these images, downsamplers, and ratios.

        :param args:       arguments
        :param args.image: names of images
        :param args.down:  names of downsamplers
        :param args.ratio: resampling ratios
        :type args:        :class:`argparse.Namespace`
        :type args.image:  `list of strings`
        :type args.down:   `list of strings`
        :type args.ratio:  `list of strings`

        :return:           names of the tables
        :rtype:            `list of strings`

        """
        # Start assembling an SQL query for the specified tables.
        query = 'SELECT name FROM TABLEDATA WHERE ('

        # Append the image names.
        if args.image:
            for image in args.image:
                query = ' '.join([query, 'image = \'{}\' OR'.format(image)])
            query = ''.join([query.rstrip(' OR'), ')'])

        # Append the downsampler names.
        if args.down:
            if args.image:
                query = ' '.join([query, 'AND ('])
            for downsampler in args.down:
                downsampler_str = 'downsampler = \'{}\' OR'.format(downsampler)
                query = ' '.join([query, downsampler_str])
            query = ''.join([query.rstrip(' OR'), ')'])

        # Append the ratios.
        if args.ratio:
            if (args.image or args.down):
                query = ' '.join([query, 'AND ('])
            for ratio in args.ratio:
                query = ' '.join([query, 'ratio = \'{}\' OR'.format(ratio)])
            query = ''.join([query.rstrip(' OR'), ')'])

        # Return the table names.
        return [table[0] for table in self.sql_fetchall(query)]

    def drop_backup(self, name):
        """Drop a backup table once it is no longer needed.

        :param name: name of the backup table to drop
        :type name:  `string`

        """
        self.sql_do('DROP TABLE {}'.format(name))

    def drop_tables(self, images, downsamplers, ratios):
        """Drop database tables.

        All tables defined by any of the images, downsamplers, or ratios are
        dropped. The TABLEDATA table is updated to reflect these changes.

        :param images:       names of the images
        :param downsamplers: names of the downsamplers
        :param ratios:       resampling ratios
        :type images:        `list of strings`
        :type downsamplers:  `list of strings`
        :type ratios:        `list of strings`

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

        :param sql:    SQL query to execute
        :param params: values to fill wildcards in the SQL statement
        :type sql:     `string`
        :type params:  `list of values`

        :return:       rows specified by the SQL query
        :rtype:        `list of dicts`

        """
        cursor = self.dbase.execute(sql, params)
        return cursor.fetchall()

    def get_error_data(self, table, upsampler, metrics_str):
        """Return a filtered row of error data.

        For the upsampler row in the table, return a dictionary containing only
        the error data for the specified metrics.

        :param table:       name of the table to query
        :param upsampler:   name of the upsampler (row) to acquire data from
        :param metrics_str: metrics to return error data for (comma-separated)
        :type table:        `string`
        :type upsampler:    `string`
        :type metrics_str:  `string`

        :return:            the filtered row of error data
        :rtype:             `dict`

        """
        sql = 'SELECT upsampler,{} FROM {} WHERE upsampler=\'{}\''
        query = sql.format(metrics_str, table, upsampler)
        cursor = self.dbase.execute(query)
        return dict(cursor.fetchone())

    def insert(self, table, row):
        """Insert a single row into the table, or update if it exists.

        :param table: name of the table
        :param row:   row data to insert
        :type table:  `string`
        :type row:    `dict`

        """
        keys = sorted(row.keys())
        values = [row[v] for v in keys]
        query = 'INSERT OR REPLACE INTO {} ({}) VALUES ({})'.format(
            table, ', '.join(keys), ', '.join('?' for i in range(len(values))))
        self.dbase.execute(query, values)
        self.dbase.commit()

    def delete(self, table, upsampler):
        """Delete a row from the table.

        :param table:     name of the table to delete from
        :param upsampler: upsampler (row) to remove from the table
        :type table:      `string`
        :type upsampler:  `string`

        """
        query = 'DELETE FROM {} where upsampler = ?'.format(table)
        self.dbase.execute(query, [upsampler])
        self.dbase.commit()

    def close(self):
        """Close the connection to the database."""
        self.dbase.close()
