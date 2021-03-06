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
        self.cur.execute("CREATE TABLE IF NOT EXISTS smac_network(id INTEGER PRIMARY KEY AUTOINCREMENT,  name_home STR, name_topic STR, id_topic STR, id_device STR, name_device STR, type_device STR, remove INT, view_topic INT, view_device INT, is_busy INT, busy_period INT, pin_device STR, pin_device_valid INT, last_updated INT, interval_online INT   )")
        self.cur.execute("CREATE TABLE IF NOT EXISTS smac_property(id INTEGER PRIMARY KEY AUTOINCREMENT, id_device STR, id_property STR, type_property STR, name_property STR, value STR, value_min STR, value_max STR, value_step STR, value_unit STR , remove INT, value_temp STR, value_last_updated STR)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS smac_command_status(id INTEGER PRIMARY KEY AUTOINCREMENT, id_topic STR, id_device STR, id_property STR, id_context, cmd STR, time INT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS smac_context_action(id INTEGER PRIMARY KEY AUTOINCREMENT, id_context STR, name_context STR, id_topic STR, id_device STR, id_property STR, value STR, comparator STR, last_updated INT, status INT, remove INT )")
        self.cur.execute("CREATE TABLE IF NOT EXISTS smac_context_trigger(id INTEGER PRIMARY KEY AUTOINCREMENT, id_context STR, id_topic STR, id_device STR, id_property STR, value STR, last_updated INT, status INT, remove INT, type_trigger )")

    def create_indexes(self, *args):
        try:
            self.cur.execute("CREATE UNIQUE INDEX smac_action_index ON smac_context_action( id_topic, id_device, id_property );")
        except Exception as e:
            print(e)

        try:
            self.cur.execute("CREATE UNIQUE INDEX smac_trigger_index ON smac_context_trigger( id_topic, id_device, id_property );")
        except Exception as e:
            print(e)

        try:
            self.cur.execute("CREATE UNIQUE INDEX smac_network_index ON smac_network( id_topic, id_device );")
        except Exception as e:
            print(e)

        try:
            self.cur.execute("CREATE UNIQUE INDEX smac_property_index ON smac_property( id_property, id_device );")
        except Exception as e:
            print(e)

        #try:
        #    self.cur.execute("CREATE UNIQUE INDEX appdata_index ON smac_appdata(key);")
        #except Exception as e:
        #    print(e)


    def remove_all_entries(self, *args):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_network')
            self.cur.execute('DELETE FROM smac_context_action')
            self.cur.execute('DELETE FROM smac_context_trigger')
            self.cur.execute('DELETE FROM smac_property')
            self.cur.execute('DELETE FROM smac_command_status')
            self.connection.commit()
        except Exception as e:
            print("eg: {}".format(e))
        finally:
            lock.release()

    # context actions
    def add_context(self, id_context, name_context, id_topic, id_device=""):
        try:
            lock.acquire(True)
            self.cur.execute(
                'REPLACE INTO smac_context_action ( id_topic, id_context, id_device, id_property, value, name_context, comparator, status, last_updated, remove) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (id_topic, id_context, id_device, "", "0", name_context, "=", 0,  int(time.time()), 0 ))
            self.connection.commit()
        except Exception as e:
            print("eg: {}".format(e))
        finally:
            lock.release()

    def remove_context(self, id_context, id_topic):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_context_action WHERE id_topic=? AND id_context=?', (id_topic, id_context))
            self.cur.execute('DELETE FROM smac_context_trigger WHERE id_topic=? AND id_context=?', (id_topic, id_context))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_context_by_topic(self, id_topic):
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_topic, id_context, name_context FROM smac_context_action WHERE id_topic=? AND remove=0', (id_topic,))
            #print("fetchall", self.cur.fetchall())
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def add_context_action(self, id_context, id_topic, id_device, id_property, name_context, value, comparator="="):
        try:
            lock.acquire(True)
            self.cur.execute(
                'REPLACE INTO smac_context_action ( id_topic, id_context, id_device, id_property, value, name_context, comparator, status, last_updated, remove) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (id_topic, id_context, id_device, id_property, value, name_context, comparator, 0,  int(time.time()), 0 ))
            self.connection.commit()
        except Exception as e:
            print("eg: {}".format(e))
        finally:
            lock.release()

    def get_action_by_context(self, id_context):
        try:
            lock.acquire(True)
            return self.cur.execute('SELECT id_device, id_property, value, comparator, status, last_updated FROM smac_context_action WHERE id_context=? AND remove=0', (id_context,)).fetchall()
            # return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_action_by_device(self, id_device, id_context):
        try:
            lock.acquire(True)
            return self.cur.execute(
                'SELECT id_topic, id_context, id_device, id_property, value, name_context FROM smac_context_action WHERE id_device=? AND id_context=? AND remove=0',(id_device,id_context)).fetchall()
            # return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_action_by_device_only(self, id_device):
        try:
            lock.acquire(True)
            self.cur.execute(
                'SELECT id_topic, id_context, id_device, id_property, value, name_context FROM smac_context_action WHERE id_device=? AND remove=0',(id_device,))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_action_by_property_value(self, id_device, id_property, value):
        try:
            lock.acquire(True)
            self.cur.execute(
                'SELECT id_topic, id_context, id_device, id_property, value FROM smac_context_action WHERE id_device=? AND id_property=? AND value=? AND remove=0',(str(id_device), str(id_property), value))
            return self.cur.fetchall()
        except Exception as e:
            print("e action", e)
        finally:
            lock.release()

    def update_action_value(self, id_topic, id_context, id_device, id_property, value):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_context_action SET value=? WHERE id_topic=? AND id_context=? AND id_device=? AND id_property=?', (value, id_topic, id_context, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_action_status(self, id_device, id_property, status=0):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_context_action SET status=? WHERE  id_device=? AND id_property=?', (status, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print("ee:", e)
        finally:
            lock.release()

    def remove_action_by_topic(self, id_topic):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_context_action WHERE id_topic=?', (id_topic,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def remove_action_by_property(self, id_topic, id_context, id_device, id_property):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_context_action WHERE id_topic=? AND id_context=? AND id_device=? AND id_property=?', (id_topic, id_context, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    # context trigger
    # type_trigger values -->
    # 0 --> property based
    # 1 --> time based
    # 2 --> location based
    def add_context_trigger(self, id_context, id_topic, id_device, id_property, value, remove=0, status=0, type_trigger="0"):
        try:
            lock.acquire(True)
            self.cur.execute(
                'REPLACE INTO smac_context_trigger ( id_topic, id_context, id_device, id_property, value, status, last_updated, remove, type_trigger) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (id_topic, id_context, id_device, id_property, value,  status, int(time.time()), remove, type_trigger ))
            self.connection.commit()
        except Exception as e:
            print("eg: {}".format(e))
        finally:
            lock.release()

    def get_trigger_by_context(self, id_context):
        try:
            lock.acquire(True)
            self.cur.execute('SELECT id_device, id_property, value, status, last_updated, type_trigger FROM smac_context_trigger WHERE id_context=? AND remove=0', (id_context,))
            return self.cur.fetchall()
            # return self.cur.fetchall()
        except Exception as e:
            print(e)
            return []
        finally:
            lock.release()

    def get_triggers_all(self):
        try:
            lock.acquire(True)
            self.cur.execute('SELECT id_topic, id_context, id_device, id_property, value, type_trigger FROM smac_context_trigger WHERE remove=0')
            return self.cur.fetchall()
        except Exception as e:
            print(e)
            return []
        finally:
            lock.release()

    def get_trigger_by_device(self, id_device):
        try:
            lock.acquire(True)
            return self.cur.execute(
                'SELECT id_topic, id_context, id_device, id_property, value, type_trigger FROM smac_context_trigger WHERE id_device=? AND remove=0',(id_device,)).fetchall()
            # return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_trigger_by_property_value(self, id_device, id_property, value):
        try:
            lock.acquire(True)
            self.cur.execute(
                'SELECT id_topic, id_context, id_device, id_property, value, type_trigger FROM smac_context_trigger WHERE id_device=? AND id_property=? AND value=? AND remove=0',( str(id_device), str(id_property), value))
            return self.cur.fetchall()
        except Exception as e:
            print(print("e trig", e))
        finally:
            lock.release()

    def update_trigger_value(self, id_topic, id_context, id_device, id_property, value):
        try:
            lock.acquire(True)
            self.cur.execute(
                'UPDATE smac_context_trigger SET value=? WHERE id_topic=? AND id_context=? AND id_device=? AND id_property=?',
                (value, id_topic, id_context, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_trigger_status(self, id_device, id_property, status=0):
        print("type(status)", status)
        print(id_device)
        print(id_property)
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_context_trigger SET status=? WHERE id_device=? AND id_property=? AND remove=0', (status, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print("e2", e)
        finally:
            lock.release()

    def remove_trigger_by_topic(self, id_topic):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_context_trigger WHERE id_topic=?', (id_topic,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def remove_trigger_by_property(self, id_topic, id_context, id_device, id_property):
        try:
            lock.acquire(True)
            self.cur.execute(
                'DELETE FROM smac_context_trigger WHERE id_topic=? AND id_context=? AND id_device=? AND id_property=?',
                (id_topic, id_context, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    # command status
    # used to handle device responses
    def add_command_status(self, id_topic, id_device, cmd, id_property="", id_context="" ):
        try:
            lock.acquire(True)
            t =  int( time.time() )
            self.cur.execute(
                'REPLACE INTO smac_command_status ( id_topic, id_device, id_context, cmd, id_property, time) VALUES (?, ?, ?, ?, ?, ?)', (id_topic, id_device, id_context, cmd, id_property, t))
            self.connection.commit()
        except Exception as e:
            print("eg: {}".format(e))
        finally:
            lock.release()

    def get_command_status(self, id_topic, id_device, id_property="", id_context=""):
        try:
            lock.acquire(True)
            r = self.cur.execute('SELECT * FROM smac_command_status WHERE id_topic=? AND id_device=? AND id_property=? AND id_context=? ORDER BY time', (id_topic, id_device, id_property, id_context)).fetchone()
            if r != None:
                return r
            # return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def remove_command_status(self, id_topic, id_device, cmd, id_property="", id_context=""):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_command_status WHERE id_topic=? AND id_device=? AND id_property=? AND id_context=? AND cmd=?', (id_topic, id_device, id_property, id_context, cmd))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def remove_command_status_all(self):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_command_status')
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()


    # change to topic
    def add_network_entry(self, id_topic, id_device, name_device, type_device, name_home="", name_topic="", remove=0, view_topic=0, view_device=0, is_busy=0, busy_period=0, pin_device="1234", pin_device_valid=1, interval_online=30):
        try:
            last_updated = int(time.time())
            lock.acquire(True)
            self.cur.execute(
                'REPLACE INTO smac_network ( name_home, name_topic, id_topic, id_device, name_device, type_device,  remove, view_topic, view_device, is_busy, busy_period, pin_device, pin_device_valid, interval_online, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', \
                (name_home, name_topic, id_topic, id_device, name_device, type_device, remove, view_topic, view_device, is_busy, busy_period, pin_device, pin_device_valid, interval_online, last_updated))
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

    def update_device_busy(self, id_device, is_busy=0, busy_period=0, *args):
        try:
            lock.acquire(True)
            print("3a")
            last_updated = int(time.time())
            self.cur.execute('UPDATE smac_network SET last_updated=?, is_busy=?, busy_period=? WHERE id_device=?', (last_updated, is_busy, busy_period, id_device))
            self.connection.commit()
            print("4a")
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_busy_devices(self, is_busy=1):
        try:
            lock.acquire(True)
            self.cur.execute('SELECT id_device, is_busy, busy_period FROM smac_network WHERE is_busy=?', ( str(is_busy) ,))
            #print('Noone')
            return self.cur.fetchall()
        except Exception as e:
            print(e)
            return []
        finally:
            lock.release()

    def get_device_busy(self, id_device):
        try:
            lock.acquire(True)
            r = self.cur.execute('SELECT is_busy FROM smac_network ORDER BY id_device', (id_device,)).fetchone()
            if r != None:
                return r[0]
            # return self.cur.fetchall()
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

    def update_pin_valid(self, id_device, pin_device_valid):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET pin_device_valid=? WHERE id_device=?',( pin_device_valid, id_device,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()



    def update_device_pin(self, id_device, pin_device):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET last_updated=?, pin_device=? WHERE id_device=?',( int(time.time()), pin_device, id_device,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_pin_device(self, id_device):
        try:
            lock.acquire(True)
            r = self.cur.execute('SELECT pin_device FROM smac_network WHERE id_device=? ORDER BY id_device', (id_device,)).fetchone()
            if r != None:
                return r[0]
            #return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_device_name(self, id_device, name_device):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET last_updated=?, name_device=? WHERE id_device=?',( int(time.time()), name_device, id_device,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_device_name(self, id_device):
        try:
            lock.acquire(True)
            r = self.cur.execute('SELECT name_device FROM smac_network WHERE id_device=?', (id_device,)).fetchone()
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

    def update_delete_all(self, this_device, value=0, ):
        try:
            lock.acquire(True)
            self.cur.execute('UPDATE smac_network SET remove=? WHERE id_device!=?', (value, this_device))
            self.cur.execute('UPDATE smac_property SET remove=? WHERE id_device!=?', (value, this_device))
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

    def delete_network_entry(self, id_topic):
        try:
            lock.acquire(True)
            self.cur.execute('DELETE FROM smac_network WHERE id_topic=?', (id_topic,))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_device_list_by_topic(self, id_topic, set=0,  *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_device, name_device, type_device, view_device, is_busy, busy_period, pin_device, pin_device_valid, interval_online, last_updated FROM smac_network WHERE id_topic=? AND remove=0 ORDER BY name_device DESC LIMIT ?,?', (id_topic, set, self.ELEMENTS_PER_PAGE))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_topic_list(self, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_topic, name_topic, view_topic FROM smac_network WHERE remove=0 ORDER BY name_topic DESC LIMIT ?,?', (set, self.ELEMENTS_PER_PAGE))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_topic_list_by_device(self, id_device, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_topic, name_home, name_topic FROM smac_network WHERE id_device=? AND remove=0 ORDER BY name_topic DESC LIMIT ?,?', (id_device, set, self.ELEMENTS_PER_PAGE))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_topic_list_not_by_device(self, id_device, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            #print(id_device)
            self.cur.execute('SELECT DISTINCT id_topic, name_home, name_topic FROM smac_network WHERE id_device!=?', (id_device,))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_topic_list_by_name_home(self, name_home, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_topic, name_home, name_topic, view_topic FROM smac_network WHERE name_home=? AND remove=0 ORDER BY name_topic DESC LIMIT ?,?', (name_home, set, self.ELEMENTS_PER_PAGE))
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_home_list(self, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT name_home, id_topic FROM smac_network WHERE remove=0')
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_property_list_by_device(self, id_device, set=0, *args ):
        set = set * self.ELEMENTS_PER_PAGE
        try:
            lock.acquire(True)
            self.cur.execute('SELECT DISTINCT id_property, name_property, type_property, value_min, value_max, value, value_temp, value_last_updated FROM smac_property WHERE id_device=? AND remove=0 LIMIT ?,?', (id_device, set, self.ELEMENTS_PER_PAGE))
            #print(a)
            return self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_property_name_by_property(self, id_device, id_property):
        try:
            lock.acquire(True)
            self.cur.execute('SELECT name_property, type_property FROM smac_property WHERE id_device=? AND id_property=?', (id_device, id_property))
            #print(d)
            #print(a)
            return self.cur.fetchone()
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
            print("e1", e)
        finally:
            lock.release()

    def update_name_property(self, id_device, id_property, name_property):
        try:
            lock.acquire(True)
            self.cur.execute(
                'UPDATE smac_property SET name_property=? WHERE id_device=? AND id_property=?', (name_property, id_device, id_property))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_value_temp_by_dev_id(self, id_device, id_property, value):
        try:
            lock.acquire(True)
            last_updated = int(time.time())
            self.cur.execute(
                'UPDATE smac_property SET value_temp=?, value_last_updated=? WHERE id_device=? AND id_property=?',(value, last_updated, id_device, id_property))
            self.cur.execute('UPDATE smac_network SET last_updated=? WHERE id_device=?', (last_updated, id_device))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_device_interval_online(self, id_device, interval):
        try:
            lock.acquire(True)
            last_updated = int(time.time())
            self.cur.execute('UPDATE smac_network SET interval_online=?, last_updated=? WHERE id_device=?', (interval, last_updated, id_device))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def update_device_last_updated(self, id_device):
        try:
            lock.acquire(True)
            last_updated = int(time.time())
            self.cur.execute('UPDATE smac_network SET last_updated=? WHERE id_device=?',
                             (last_updated, id_device))
            self.connection.commit()
        except Exception as e:
            print(e)
        finally:
            lock.release()

    def get_device_interval_online(self, id_device):
        try:
            lock.acquire(True)
            r = self.cur.execute('SELECT interval_online FROM smac_network WHERE id_device=?', (id_device,)).fetchone()
            if r != None:
                return r[0]
            #return self.cur.fetchall()
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