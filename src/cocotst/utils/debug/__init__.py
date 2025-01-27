from typing import Any, Type
from pydantic import BaseModel
import inspect


def format_value(value: Any) -> str:
    """格式化值的显示，将不同类型的值转换为易读的字符串形式"""
    if isinstance(value, bool):
        return "✓" if value else "✗"
    elif value is None:
        return "None"
    elif isinstance(value, BaseModel):
        return f"[{value.__class__.__name__}]"
    return str(value)


def get_class_doc(model: Type[BaseModel]) -> str:
    """获取类的文档字符串"""
    if model.__doc__:
        return inspect.cleandoc(model.__doc__)
    return ""


def get_field_doc(model: Type[BaseModel], field_name: str) -> str:
    """获取字段的文档字符串

    通过检查模型的 __annotations__ 和类属性来获取字段文档，
    同时避免获取到基础类型的内建文档。
    """
    # 首先检查类属性是否存在文档注释
    try:
        # 获取类中定义的原始属性
        class_vars = vars(model)
        if field_name in class_vars:
            # 获取属性定义
            field_value = class_vars[field_name]
            # 检查是否有文档字符串
            if isinstance(field_value, property) and field_value.__doc__:
                return inspect.cleandoc(field_value.__doc__)
    except (AttributeError, TypeError):
        pass

    # 检查私有命名空间中的文档字符串
    try:
        private_doc = getattr(model, f"_{model.__name__}__{field_name}", None)
        if isinstance(private_doc, str):
            return inspect.cleandoc(private_doc)
    except AttributeError:
        pass

    # 如果字段是嵌套的 BaseModel，获取其类文档
    try:
        field = model.model_fields[field_name]
        if issubclass(field.annotation, BaseModel):
            class_doc = get_class_doc(field.annotation)
            if class_doc:
                return class_doc
    except (KeyError, AttributeError, TypeError):
        pass

    # 最后尝试从 model_fields 获取 description
    try:
        field = model.model_fields[field_name]
        if field.description:
            return field.description
    except (KeyError, AttributeError):
        pass

    return ""


def print_debug_tree(
    config: BaseModel, indent: str = "", is_last: bool = True, parent_prefix: str = ""
) -> str:
    """递归地将配置对象转换为树形结构字符串

    生成一个层次清晰的配置树，包含值和相关文档注释。
    """
    output = []
    curr_indent = parent_prefix + ("└── " if is_last else "├── ")
    next_prefix = parent_prefix + ("    " if is_last else "│   ")

    # 添加根节点名称和类文档
    if indent == "":
        class_name = config.__class__.__name__
        class_doc = get_class_doc(config.__class__)
        output.append(f"{class_name}{' # ' + class_doc if class_doc else ''}")
        curr_indent = ""
        next_prefix = ""

    # 获取所有字段
    fields = list(config.model_fields.items())

    # 处理每个字段
    for idx, (field_name, field) in enumerate(fields):
        value = getattr(config, field_name)
        is_last_field = idx == len(fields) - 1

        # 获取字段文档
        doc = get_field_doc(config.__class__, field_name)
        doc_suffix = f" # {doc}" if doc else ""

        # 处理嵌套的配置对象
        if isinstance(value, BaseModel):
            output.append(f"{curr_indent}{field_name}{doc_suffix}")
            subtree = print_debug_tree(value, indent + "  ", is_last_field, next_prefix)
            output.append(subtree)
        else:
            output.append(f"{curr_indent}{field_name}: {format_value(value)}{doc_suffix}")

    return "\n".join(output)
