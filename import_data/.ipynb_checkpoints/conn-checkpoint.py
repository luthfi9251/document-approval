import pymysql.cursors
import numpy as np

pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.encoders[np.float64] = pymysql.converters.escape_float
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)

mysql_host = 'psidevel.dinus.ac.id'
mysql_user = 'webdinus'
mysql_passwd = 'passwordweb'
mysql_db = 'siakad'

try:    
    from local_ import *
except ImportError:
    pass

mysql = pymysql.connect(host=mysql_host, user=mysql_user,
                        password=mysql_passwd, db=mysql_db,
                        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
cur = mysql.cursor()
