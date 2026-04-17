from typing import Any

from fastapi.responses import JSONResponse

SUCCESS = 200
FAIL = 500


def write_information(code: int, data: any, msg: str):
    data = {
        "code": code,
        "data": data,
        "msg": msg
    }
    if code == SUCCESS:
        return data
    return JSONResponse(content=data)


# 失败返回，带数据
def fail_correctly_data(data: any, message: str):
    return write_information(FAIL, data, message)


# 成功返回，带数据
def success_correctly_data(data: any, message: str):
    return write_information(SUCCESS, data, message)


# 失败返回，不带数据
def fail_correctly(message: str):
    return write_information(FAIL, None, message)


# 成功返回，不带数据
def success_correctly(message: str):
    return write_information(SUCCESS, None, message)


# 完全自定义返回信息
def customization_correctly(code: int, data: any, msg: str):
    return JSONResponse(content={
        "code": code,
        "data": data,
        "msg": msg
    })
