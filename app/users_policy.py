from flask_login import current_user

class UsersPolicy:
    print("WE ARE HERE policy")
    
    def __init__(self, event=None):
        self.event = event

    def managing(self):
        return current_user.is_admin()
    
    def edit(self):
        return self.event.user_id == int(current_user.id)
    
    def delete(self):
        return self.event.user_id == int(current_user.id)
    