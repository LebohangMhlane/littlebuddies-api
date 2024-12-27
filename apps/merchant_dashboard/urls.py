from django.urls import path
from .views import *

urlpatterns = [
    path('manage-branch-dashboard/<int:branchId>', ManageBranchView.as_view(), name='manage_branch_dashboard'),
]
