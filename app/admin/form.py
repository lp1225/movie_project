# encoding: utf-8
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField, SubmitField, FileField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, ValidationError, EqualTo
from models import Admin, Auth


class LoginForm(FlaskForm):
    account = StringField(
        label='账号',
        validators=[DataRequired('请输入账号')],
        description='账号',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入账号',
            # 'required':'required'
        }
    )
    pwd = PasswordField(
        label='密码',
        validators=[DataRequired('请输入密码')],
        description='密码',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入密码',
            # 'required': 'required'
        }
    )
    submit = SubmitField(
        '登录',
        render_kw={
            'class': 'btn btn-primary btn-block btn-flat'
        }
    )


    def validate_account(self, field):
        account = field.data
        admin_len = Admin.query.filter_by(name=account).count()
        if admin_len == 0:
            raise ValidationError('该用户不存在')


class TagForm(FlaskForm):
    name = StringField(
        label='标签',
        validators=[DataRequired('请输入标签名称！')],
        description='标签',
        render_kw={
          'class':'form-control',
          'id':'input_name',
          'placeholder':'请输入标签名称'
        }
    )

    submit =SubmitField(
        '编辑',
        render_kw={
            'class': 'btn btn-primary'
        }
    )


class MovieForm(FlaskForm):
    title = StringField(
        label='片名',
        validators=[DataRequired('请输入片名')],
        description='片名',
        render_kw={
            'class': 'form-control',
            'id': 'input_title',
            'placeholder': '请输入片名'
        }
    )

    url = FileField(
        label='文件',
        validators=[DataRequired('请上传文件')],
        description='文件',
    )

    info = TextAreaField(
        label='介绍',
        validators=[DataRequired('请输入简介')],
        description='介绍',
        render_kw={
           'class': 'form-control',
           'rows': '10',
           'id': 'input_info'
        }
    )

    logo = FileField(
        label='封面',
        validators=[DataRequired('请上传封面')],
        description='封面',
    )

    star = SelectField(
        label='星级',
        validators=[DataRequired('请选择星级')],
        description='星级',
        coerce=int,
        choices=[(1, '一星'), (2, '二星'), (3, '三星'), (4, '四星'), (5, '五星')],
        render_kw={
            'class': 'form-control',
        }
    )

    tag_id = SelectField(
        label='标签',
        validators=[DataRequired('请选择标签')],
        description='标签',
        coerce=int,
        choices='',
        render_kw={
            'class': 'form-control',
        }
    )
    # def __init__(self, *args, **kwargs):
    #     self.tag_id.choices = [(v.id, v.name) for v in Tag.query.all()]
    #     super(MovieForm,self).__init__(*args, **kwargs)


    area = StringField(
        label='地区',
        validators=[DataRequired('请输入地区')],
        description='地区',
        render_kw={
            'class': 'form-control',
            'id': 'input_area',
            'placeholder': '请输入地区'
        }
    )

    length = StringField(
        label='片长',
        validators=[DataRequired('请输入片长')],
        description='片长',
        render_kw={
            'class': 'form-control',
            'id': 'input_length',
            'placeholder': '请输入片长'
        }
    )

    area = StringField(
        label='地区',
        validators=[DataRequired('请输入地区')],
        description='地区',
        render_kw={
            'class': 'form-control',
            'id': 'input_area',
            'placeholder': '请输入地区'
        }
    )

    release_time = StringField(
        label='上映时间',
        validators=[DataRequired('请输入上映时间')],
        description='上映时间',
        render_kw={
            'class': 'form-control',
            'id': 'input_release_time',
            'placeholder': '请输入上映时间'
        }
    )

    submit = SubmitField(
        '添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )


class PreviewForm(FlaskForm):
    title = StringField(
        label='预告标题',
        validators=[DataRequired('请输入预告标题')],
        description='标题',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入预告标题'
        }
    )

    logo = FileField(
        label='预告封面',
        validators=[DataRequired('请上传预告封面')],
        description='预告封面'
    )

    submit = SubmitField(
        '添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )


class PwdForm(FlaskForm):
    old_pwd = PasswordField(
        label='旧密码',
        validators = [DataRequired('请输入旧密码')],
        description='旧密码',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入旧密码'
        }
    )

    new_pwd = PasswordField(
        label='新密码',
        validators=[DataRequired('请输入新密码')],
        description='新密码',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入新密码'
        }
    )

    submit = SubmitField(
        '添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )

    # 验证旧密码是否存在
    def validate_old_pwd(self, field):
        from flask import session
        pwd = field.data
        name = session['admin']
        admin = Admin.query.filter_by(name=name).first()
        if not admin.check_pwd(pwd):
            raise ValidationError('旧密码不存在')


class AuthForm(FlaskForm):
    name = StringField(
        label="权限名称",
        validators={
            DataRequired("请输入权限名称!")
        },
        description="权限名称",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入权限名称!"
        }
    )
    url = StringField(
        label="权限地址",
        validators={
            DataRequired("请输入权限地址")
        },
        description="权限名称",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入权限地址"
        }
    )
    submit = SubmitField(
        '添加',
        render_kw={
            "class": "btn btn-primary",
        }
    )


# 角色表单
class RoleForm(FlaskForm):
    name = StringField(
        label='角色名称',
        validators=[DataRequired('请输入角色名称')],
        description='角色名称',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入角色名称'
        }
    )

    auths = SelectMultipleField(
        label="权限列表",
        validators={
            DataRequired("请选择权限!")
        },
        description="权限列表",
        coerce=int,
        render_kw={
            "class": "form-control",
        }
    )

    submit = SubmitField(
        '编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class AdminForm(FlaskForm):
    name = StringField(
        label="管理员名称",
        validators=[
            DataRequired("请输入管理员名称!")
        ],
        description="管理员名称",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入管理员名称!",
        }
    )

    pwd = PasswordField(
        label="管理员密码",
        validators=[
            DataRequired("请输入管理员密码!")
        ],
        render_kw={
            "class": "form-control",
            "placeholder": "请输入管理员密码!",
        }
    )

    rep_pwd = PasswordField(
        label="管理员重复密码",
        validators=[
            DataRequired("请输入管理员重复密码!"),
            EqualTo("pwd", message="输入的密码不一致!")
        ],
        render_kw={
            "class": "form-control",
            "placeholder": "请输入管理员重复密码!",
        }
    )

    role_id = SelectField(
        label="所属角色",
        coerce=int,
        render_kw={
            "class": "form-control",
        }
    )

    submit = SubmitField(
        '编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )



