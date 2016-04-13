# -*- coding: utf-8 -*-
from mana_api import db

# 流量主表
class netflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(80))
    total_in = db.Column(db.String(120))
    total_out = db.Column(db.String(120))
    max_in_rate = db.Column(db.Float)
    max_in_rate_date = db.Column(db.DateTime)
    max_out_rate = db.Column(db.Float)
    max_out_rate_date = db.Column(db.DateTime)
    region = db.Column(db.String(120))
    project_id = db.Column(db.String(120))

    def __repr__(self):
        return '<Project %s>' % self.project_id

# 流量详细表
class netrate_project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    in_rate = db.Column(db.Float)
    out_rate = db.Column(db.Float)
    begin_rate_date = db.Column(db.DateTime)
    end_rate_date = db.Column(db.DateTime)
    region = db.Column(db.String(80))
    project_id = db.Column(db.String(80))

    def __repr__(self):
        return '<Project(Detail) %r>' % self.project_id

# 物理机固定信息表
class pm_firmware(db.Model):
    __bind_key__ = 'cmdb'
    id = db.Column(db.Integer)
    snid = db.Column(db.String(255), primary_key=True)
    asset_id = db.Column(db.String(255))
    manufacturer = db.Column(db.String(255))
    state = db.Column(db.String(64), default='active')
    create_at = db.Column(db.DateTime)
    update_at = db.Column(db.DateTime)


# 物理机非固定信息表
class pm_variable(db.Model):
    __bind_key__ = 'cmdb'
    id = db.Column(db.Integer, primary_key=True)
    snid = db.Column(db.String(255))
    host_name = db.Column(db.String(255))
    os_type = db.Column(db.String(255))
    region = db.Column(db.String(64))
    status = db.Column(db.String(64), default='running')
    cpu_num = db.Column(db.Integer)
    mem_size = db.Column(db.Integer)
    disk_size = db.Column(db.Integer)
    ip = db.Column(db.String(255))
    ilo_ip = db.Column(db.String(255))
    ilo_user = db.Column(db.String(255), default='root')
    ilo_passwd = db.Column(db.String(255), default='ztgame@123')
    ilo_state = db.Column(db.Integer)
    remark = db.Column(db.String(255))
    update_at = db.Column(db.DateTime)


# 物理机与项目对应关系表
class pm_relation(db.Model):
    __bind_key__ = 'cmdb'
    id = db.Column(db.Integer, primary_key=True)
    snid = db.Column(db.String(255))
    tenant_id = db.Column(db.String(255))
    update_at = db.Column(db.DateTime)


# 物理机迁移订单表
class pm_orders(db.Model):
    __bind_key__ = 'cmdb'
    id = db.Column(db.Integer, primary_key=True)
    snids = db.Column(db.String(255))
    resource_project = db.Column(db.String(255))
    dest_project = db.Column(db.String(255))
    user = db.Column(db.String(255))
    state = db.Column(db.String(255), default='unfinished')
    warnning_times = db.Column(db.String(255))
    create_at = db.Column(db.DateTime)
    update_at = db.Column(db.DateTime)


# 新计费表
class pm_expense(db.Model):
    __bind_key__ = 'cmdb'
    id = db.Column(db.Integer, primary_key=True)
    snid = db.Column(db.String(255))
    price = db.Column(db.Float)
    tenant_id = db.Column(db.String(255))
    region = db.Column(db.String(255))
    update_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Project(Detail) %r>' % self.system_snid


# 联系人表
class pm_contact_list(db.Model):
    __bind_key__ = 'cmdb'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(255))
    name = db.Column(db.String(255))


# 监控数据表
class pm_monitors(db.Model):
    __bind_key__ = 'cmdb'
    id = db.Column(db.Integer, primary_key=True)
    system_snid = db.Column(db.String(255))
    info = db.Column(db.Text)
    update_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Project(Detail) %r>' % self.system_snid

# 虚拟机计费表
class expense_virtual(db.Model):
    __bind_key__ = 'cloud'
    __tablename__ = 'expense_virtual'
    id = db.Column(db.Integer, primary_key=True)
    locationID = db.Column(db.String(64))
    projectID = db.Column(db.String(64))
    serverID = db.Column(db.String(64))
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    day = db.Column(db.Integer)
    value = db.Column(db.Float)
    personID = db.Column(db.String(32))
    display_name = db.Column(db.String(128))


