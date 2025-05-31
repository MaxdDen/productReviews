from fastapi import HTTPException, status

def check_object_permission(obj, current_user):
    if current_user.is_superuser:
        return  # доступ есть всегда
    if not obj or obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к этому ресурсу."
        )
    