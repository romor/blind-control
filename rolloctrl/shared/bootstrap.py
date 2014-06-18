"""This module provides utility functions used during application initialization."""

import os, os.path
import sys
import logging
import configparser
import sqlalchemy

# self-defined modules
from diagnos.lib.dbhelper import DbHelper


def init_config():
    """reads the configuration files and sets the default environment"""
    # determine config file path, which is one levels above the called script
    basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    configpars = configparser.ConfigParser()
    configpars.read(os.path.join(basepath, "diagnos.conf"))
    environment = os.getenv('DIAGNOS_ENV', 'DEFAULT')   # default if not set
    config = configpars[environment]
    config['basepath'] = basepath
    return config


def init_logging(config):
    """setup logging to file and console"""
    # extract filename
    scriptname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    # setup root logger
    # we assume a higher log level on console logger
    logging.getLogger().setLevel(config['log_level_console'].upper())

    # create file and console handler
    log_file = logging.FileHandler(os.path.join(config['log_dir'],
                                                scriptname + '.log'))
    log_file.setLevel(config['log_level_file'].upper())
    log_console = logging.StreamHandler()
    log_console.setLevel(config['log_level_console'].upper())

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    log_file.setFormatter(formatter)

    # add the handlers to the logger
    logging.getLogger().addHandler(log_file)
    logging.getLogger().addHandler(log_console)

    #logging.getLogger().debug('logging started')


def init_db(config):
    """connects to database."""
    try:
        # create and connect to database engine
        db_path = config.get('db_path')
        db_url = "sqlite:///{}".format(db_path if db_path else 'db.sqlite')
        engine = sqlalchemy.create_engine(db_url, echo=False)
        db = engine.connect()
        # setup sqlite
        db.execute('PRAGMA journal_mode=PERSIST').close()
        db.execute('PRAGMA foreign_keys=ON').close()

    except Exception as ex:
        logging.getLogger().error(str(ex))
        raise Exception("Error connecting to database")

    return db


def check_database(db):
    """checks database availability and version of the database."""
    sql = "SELECT version FROM t_version"
    version = DbHelper(db).fetch_one(sql)
    if version != 1:
        raise Exception("Database check error.")


def init_tables():
    """creates sqlalchemy handlers for DB tables."""
    tables = {}
    metadata = sqlalchemy.MetaData()
    tables['t_sensor'] = sqlalchemy.Table('t_sensor', metadata,
        sqlalchemy.Column('sens_id', sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column('sens_datapoint', sqlalchemy.Integer),
        sqlalchemy.Column('sens_serial', sqlalchemy.Integer),
        sqlalchemy.Column('sens_fk_lastdata', sqlalchemy.Integer,
                          sqlalchemy.ForeignKey('t_data.data_id')),
    )
    tables['t_data'] = sqlalchemy.Table('t_data', metadata,
        sqlalchemy.Column('data_id', sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column('data_fk_sensor', sqlalchemy.Integer,
                          sqlalchemy.ForeignKey('t_sensor.sens_id')),
        sqlalchemy.Column('data_timestamp', sqlalchemy.DateTime),
        sqlalchemy.Column('data_temperature', sqlalchemy.Float),
        sqlalchemy.Column('data_pcb_temp', sqlalchemy.Float),
        sqlalchemy.Column('data_voltage', sqlalchemy.Float),
        sqlalchemy.Column('data_rssi', sqlalchemy.Integer),
    )
    tables['t_data_historical'] = sqlalchemy.Table('t_data_historical', metadata,
        sqlalchemy.Column('hist_id', sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column('hist_fk_sensor', sqlalchemy.Integer,
                          sqlalchemy.ForeignKey('t_sensor.sens_id')),
        sqlalchemy.Column('hist_aggregate', sqlalchemy.Integer),
        sqlalchemy.Column('hist_data', sqlalchemy.Integer),
        sqlalchemy.Column('hist_timestamp', sqlalchemy.Date),
        sqlalchemy.Column('hist_value', sqlalchemy.Float),
    )
    tables['t_site'] = sqlalchemy.Table('t_site', metadata,
        sqlalchemy.Column('site_id', sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column('site_name', sqlalchemy.String),
        sqlalchemy.Column('site_ambienttemperature', sqlalchemy.Float),
    )
    tables['t_section'] = sqlalchemy.Table('t_section', metadata,
        sqlalchemy.Column('sect_id', sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column('sect_fk_site', sqlalchemy.Integer,
                          sqlalchemy.ForeignKey('t_site.site_id')),
        sqlalchemy.Column('sect_name', sqlalchemy.String),
        sqlalchemy.Column('sect_type', sqlalchemy.String),
        sqlalchemy.Column('sect_distrBarDirVertical', sqlalchemy.Boolean),
        sqlalchemy.Column('sect_mainBusbarDouble', sqlalchemy.Boolean),
        sqlalchemy.Column('sect_NWire', sqlalchemy.String),
        sqlalchemy.Column('sect_mainBusbarPos', sqlalchemy.String),
        sqlalchemy.Column('sect_split', sqlalchemy.Boolean),
        sqlalchemy.Column('sect_mainBusbar2ndDouble', sqlalchemy.Boolean),
        sqlalchemy.Column('sect_connectionDirTop', sqlalchemy.Boolean),
        sqlalchemy.Column('sect_position', sqlalchemy.Integer),
        sqlalchemy.Column('sect_width', sqlalchemy.Integer),
        sqlalchemy.Column('sect_height', sqlalchemy.Integer),
        sqlalchemy.Column('sect_depth', sqlalchemy.Integer),
        sqlalchemy.Column('sect_dropperBusbarNWire', sqlalchemy.Boolean),
    )
    tables['t_position'] = sqlalchemy.Table('t_position', metadata,
        sqlalchemy.Column('pos_id', sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column('pos_description', sqlalchemy.String),
        sqlalchemy.Column('pos_desc_short', sqlalchemy.String),
        sqlalchemy.Column('pos_phase', sqlalchemy.String),
        sqlalchemy.Column('pos_x', sqlalchemy.Float),
        sqlalchemy.Column('pos_y', sqlalchemy.Float),
        sqlalchemy.Column('pos_z', sqlalchemy.Integer),
        sqlalchemy.Column('pos_direction', sqlalchemy.String),
        sqlalchemy.Column('pos_length', sqlalchemy.Float),
        sqlalchemy.Column('pos_isMicropelt', sqlalchemy.Boolean),
        sqlalchemy.Column('pos_tmax', sqlalchemy.Float),
    )
    tables['t_equip'] = sqlalchemy.Table('t_equip', metadata,
        sqlalchemy.Column('equ_fk_sensor', sqlalchemy.Integer,
                          sqlalchemy.ForeignKey('t_sensor.sens_id')),
        sqlalchemy.Column('equ_fk_section', sqlalchemy.Integer,
                          sqlalchemy.ForeignKey('t_section.sect_id')),
        sqlalchemy.Column('equ_fk_position', sqlalchemy.Integer,
                          sqlalchemy.ForeignKey('t_position.pos_id')),
        sqlalchemy.Column('equ_equip_sens', sqlalchemy.Boolean),
        sqlalchemy.Column('equ_comment', sqlalchemy.String),
    )
    tables['t_module'] = sqlalchemy.Table('t_module', metadata,
        sqlalchemy.Column('mod_id', sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column('mod_fk_section', sqlalchemy.Integer,
                          sqlalchemy.ForeignKey('t_section.sect_id')),
        sqlalchemy.Column('mod_name', sqlalchemy.String),
        sqlalchemy.Column('mod_type', sqlalchemy.String),
        sqlalchemy.Column('mod_position', sqlalchemy.Integer),
        sqlalchemy.Column('mod_hight', sqlalchemy.Integer),
        sqlalchemy.Column('mod_parameter', sqlalchemy.Integer),
    )
    tables['t_simulation_ctrl'] = sqlalchemy.Table('t_simulation_ctrl', metadata,
        sqlalchemy.Column('sim_id', sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column('sim_enabled', sqlalchemy.Boolean),
        sqlalchemy.Column('sim_sigma', sqlalchemy.Float),
        sqlalchemy.Column('sim_offset', sqlalchemy.Float),
        sqlalchemy.Column('sim_tau', sqlalchemy.Float),
    )

    return tables
