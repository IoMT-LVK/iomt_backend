import jwt
import hashlib
import os
import settings

import numpy as np

def encode_token(data={}, secret=settings.JWT_KEY, **extra):
    return jwt.encode(data | extra, secret, algorithm='HS256')

def decode_token(token, secret=settings.JWT_KEY):
    return jwt.decode(token, secret, algorithms=['HS256'])

def decode_compressed(data: list, kernel):
    data: np.ndarray = np.array(data)
    for i in range(1, data.shape[1]):
        data[:, i] = data[:, i] @ kernel
    return data.tolist()

def hash_password(pwd, salt=None):
    if len(pwd) > settings.PASSWORD_MAX_LEN:
        raise ValueError()
    salt = salt or os.urandom(settings.PASSWORD_HASH_SALT_LEN)
    pwd_hash = hashlib.scrypt(
        pwd.encode(),
        salt=salt,
        n=settings.PASSWORD_HASH_COST,
        r=settings.PASSWORD_HASH_BLOCK_SIZE,
        p=settings.PASSWORD_HASH_PARALLEL,
        dklen=settings.PASSWORD_HASH_LEN,
    )
    return pwd_hash, salt

def create_chart(x, y, title, x_name, y_name, hover_tool=None,
                     width=1200, height=300):
    """Создаёт график ЭКГ.
        Принимает данные в виде словаря, подпись для графика,
        названия осей и шаблон подсказки при наведении.
    """
    source = ColumnDataSource(dict(x=x, y=y))
    #xdr = FactorRange(factors=data[x_name])
    #ydr = Range1d(start=0,end=max(data[y_name])*1.5)

    tools = []
    if hover_tool:
        tools = [hover_tool,]

    plot = figure(title=title, plot_width=width,
                  plot_height=height, h_symmetry=False, v_symmetry=False,
                  min_border=0, toolbar_location="above", tools=tools,
                  responsive=True, outline_line_color="#666666")

    glyph = Line(x=x_name, top=y_name, bottom=0, width=.8,
                 fill_color="#e12127")
    plot.add_glyph(source, glyph)

    xaxis = LinearAxis()
    yaxis = LinearAxis()

    plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))
    plot.toolbar.logo = None
    plot.min_border_top = 0
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = "#999999"
    plot.yaxis.axis_label = "Bugs found"
    plot.ygrid.grid_line_alpha = 0.1
    plot.xaxis.axis_label = "Days after app deployment"
    plot.xaxis.major_label_orientation = 1
    return plot