import sqlite3
import threading
import time

from smac_limits import *


lock = threading.Lock()

class Database():
    ELEMENTS_PER_PAGE = 10
    db_path = "db.sqlite3"
    ID = 0

    def __init__(self, DB_path=db_path):
        self.connection = sqlite3.connect(DB_path, check_same_thread=False)
        self.cur = self.connection.cursor()
        self.create_tables()
        self.create_indexes()

    def create_tables(self, *args):
        # new table
        self.cur.execute("CREATE TABLE IF NOT EXISTS smac_network(id INTEGER PRIMARY KEY AUTOINCREMENT,  name_home STR, name_topic STR, id_topic STR, id_device STR, name_device STR, type_device STR, remove INT, view_topic INT, view_device INT, is_busy INT, pin_device STR, pin_device_valid INT   )")
        self.cur.execute("CREATE TABLE IF NOT EXISTS smac_property(id INTEGER PRIMARY KEY AUTOINCREMENT, id_device STR, id_property STR, type_property STR, name_property STR, value STR, value_min STR, value_max STR, value_step STR, value_unit STR , remove INT, value_temp STR, value_last_updated STR)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS smac_appdata(id INTEGER PRIMARY KEY AUTOINCREMENT, key STR, value STR)")

    def create_indexes(self, *args):
        try:
            self.cur.execute("CREATE UNIQUE INDEX smac_network_index ON smac_network( id_topic, id_device );")
        except Exception as e:
            print(e)

        try:
            self.cur.execute("CREATE UNIQUE INDEX smac_property_index ON smac_property( id_property, id_device );")
        except Exception as e:
            print(e)

        try:
            self.cur.execute("CREATE UNIQUE INDEX appdata_index ON smac_appdata(key);")
        except Exception as e:
            print(e)


    def add_network_entry(self, id_topic, id_device, name_device, type_device, name_home="", name_topic="", remove=0, view_topic=0, view_device=0, is_busy=0, pin_device="1234", pin_device_valid=1):
        try:
            lock.acquire(True)
            self.cur.execute(
                'REPLACE INTO smac_network ( name_home, name_topic, id_topic, id_device, name_device, type_device,  remove, view_topic, view_device, is_busy, pin_device, pin_device_valid) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', \
                (name_home, name_topic, id_topic, id_device, name_device, type_device, remove, view_topic, view_device, is_busy, pin_device, pin_device_valid))
            self.connection.commit()
        except Exception as e:
            print("eg: {}".format(e) )
        finally:
            lock.release()

    def set_topic_view(self, id_topic, view_topic):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET view_topic=? WHERE id_topic=?',(view_topic,  id_topic))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_device_busy(self, id_device, is_busy=0, *args):
        try:
            lock.acquire(True)
            print("3a")
            self.cur.execute('UPDATE smac_network SET is_busy=? WHERE id_device=?',( is_busy, id_device))
            self.connection.commit()
            print("4a")
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_pin_valid_by_device(self, id_device):
        try:
            lock.acquire(True)
            r = self.cur.execute('SELECT pin_device_valid FROM smac_network ORDER BY id_device', (id_device,)).fetchone()
            if r != None:
                return r[0]
            #return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_pin_valid_by_device(self, id_device, pin_device_valid):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET pin_device=? WHERE id_device=?',( pin_device_valid, id_device,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_device_busy(self, id_device):
        try:
            lock.acquire(True)
            r = self.cur.execute('SELECT is_busy FROM smac_network ORDER BY id_device', (id_device,)).fetchone()
            if r != None:
                return r[0]
            #return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_device_pin(self, id_device, pin_device):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET pin_device=? WHERE id_device=?',( pin_device, id_device,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_pin_device(self, id_device):
        try:
            lock.acquire(True)
            r = self.cur.execute('SELECT pin_device FROM smac_network ORDER BY id_device', (id_device,)).fetchone()
            if r != None:
                return r[0]
            #return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def set_device_view(self, id_topic, id_device, view_device):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET view_device=? WHERE id_device=? AND id_topic=?',(view_device, id_device, id_topic))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_network_entry(self, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT * FROM smac_network ORDER BY name_topic DESC LIMIT ?,?', (set, self.ELEMENTS_PER_PAGE))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_device_by_delete_field(self, id_device, value=0):
        try:
            lock.acquire(True)
            self.cur.execute('SELECT id_topic FROM smac_network WHERE id_device=? AND remove=?', (id_device, value,))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()


    def delete_network_entry_by_device(self, id_device, remove=1):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_network WHERE id_device=? AND remove=?', (id_device, remove))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_delete_by_topic_id(self, id_device, id_topic, value=0):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET remove=? WHERE id_device=? AND id_topic=?', (value, id_device, id_topic))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()


    def update_delete_by_dev_id(self, id_device,  value=0, SET_PROPERTY=False):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET remove=? WHERE id_device=?', (value, id_device))
            if SET_PROPERTY:
                self.cur.execute('UPDATE smac_property SET remove=? WHERE id_device=?', (value, id_device))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_delete_by_prop_id(self, id_device, id_property,  value=0):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_property SET remove=? WHERE id_device=? AND id_property=?', (value, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def delete_network_entry_by_topic(self, id_topic, id_device):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_network WHERE id_topic=? AND id_device=?', (id_topic, id_device))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()


    def get_device_list_by_topic(self, id_topic, set=0,  *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_device, name_device, view_device, is_busy, pin_device, pin_device_valid FROM smac_network WHERE id_topic=? ORDER BY name_device DESC LIMIT ?,?', (id_topic, set, self.ELEMENTS_PER_PAGE))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_topic_list(self, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_topic, name_topic, view_topic FROM smac_network ORDER BY name_topic DESC LIMIT ?,?', (set, self.ELEMENTS_PER_PAGE))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_topic_list_by_device(self, id_device, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_topic, name_topic FROM smac_network WHERE id_device=? ORDER BY name_topic DESC LIMIT ?,?', (id_device, set, self.ELEMENTS_PER_PAGE))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()


    def get_property_list_by_device(self, id_device, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_property, name_property, type_property, value_min, value_max, value, value_temp, value_last_updated FROM smac_property WHERE id_device=? LIMIT ?,?', (id_device, set, self.ELEMENTS_PER_PAGE))
            #print(a)
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    # add a property
    def add_property(self, id_device, id_property, type_property, name_property, value=0, value_temp=0, value_min=0, value_max=1, value_step=1, value_unit="" ,remove=0 ):
        try:
            lock.acquire(True)
            value_lastUpdated = time.time()
            self.cur.execute(
                'REPLACE INTO smac_property ( id_device, id_property, type_property, name_property, value, value_min, value_max, value_step, value_unit, remove, value_temp, value_last_updated) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', \
                (id_device, id_property, type_property, name_property, value, value_min, value_max, value_step, value_unit, remove, value_temp, value_lastUpdated))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_property_by_delete_field(self, id_device, value=0):
        try:
            lock.acquire(True)
            self.cur.execute('SELECT id_property FROM smac_property WHERE id_device=? AND remove=?', (id_device, value,))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_value_property_by_dev_id(self, id_device, id_property, value):
        try:
            lock.acquire(True)
            self.cur.execute(
                'UPDATE smac_property SET value=? WHERE id_device=? AND id_property=?', (value, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_value_temp_by_dev_id(self, id_device, id_property, value):
        try:
            lock.acquire(True)
            last_updated = time.time()
            self.cur.execute(
                'UPDATE smac_property SET value_temp=?, value_last_updated=? WHERE id_device=? AND id_property=?',(value, last_updated, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()


    # get property
    def get_property(self, id_device):
        try:
            lock.acquire(True)
            self.cur.execute('SELECT * FROM smac_property WHERE id_device=?', (id_device,))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_value_by_property(self, id_device, id_property):
        try:
            lock.acquire(True)
            v = self.cur.execute('SELECT value FROM smac_property WHERE id_device=? AND id_property=?', (id_device,id_property)).fetchone()
            if v != None:
                return v[0]
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_value_temp_by_property(self, id_device, id_property):
        try:
            lock.acquire(True)
            v = self.cur.execute('SELECT value_temp, value_last_updated FROM smac_property WHERE id_device=? AND id_property=?', (id_device,id_property)).fetchone()
            if v != None:
                return v[0]
        except Exception as e:
            print(e)
        finally:
            lock.release()


    def delete_property(self, id_device):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_property WHERE id_device=?', (id_device,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def delete_property_by_device(self, id_device, remove=1):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_property WHERE id_device=? AND remove=?', (id_device, remove))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()


db = Database()