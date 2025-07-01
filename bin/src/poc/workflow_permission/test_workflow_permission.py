"""
ワークフロー権限システムの要件仕様テスト
TDD Red Phase - 失敗するテストから開始
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from workflow_permission_system import WorkflowPermissionSystem


class TestOrganizationApprovalWorkflow:
    """組織承認ワークフローの要件テスト"""
    
    def test_組織階層を作成できる(self):
        """組織階層（部長→課長→担当者）を構築できる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        
        # Act
        org_id = system.create_organization("開発部", "department")
        manager_id = system.create_employee("山田部長", "部長", org_id)
        chief_id = system.create_employee("鈴木課長", "課長", org_id)
        member_id = system.create_employee("田中担当", "担当者", org_id)
        
        system.set_supervisor(member_id, chief_id)
        system.set_supervisor(chief_id, manager_id)
        
        # Assert
        assert system.get_supervisor(member_id) == chief_id
        assert system.get_supervisor(chief_id) == manager_id
        assert system.get_supervisor(manager_id) is None
    
    def test_要件提出で自動的に上司が承認者になる(self):
        """要件を提出すると直属の上司が自動的に承認者に設定される"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        org_id = system.create_organization("開発部", "department")
        chief_id = system.create_employee("鈴木課長", "課長", org_id)
        member_id = system.create_employee("田中担当", "担当者", org_id)
        system.set_supervisor(member_id, chief_id)
        
        # Act
        req_id = system.create_requirement("新機能追加", member_id)
        approvers = system.get_approvers(req_id)
        
        # Assert
        assert len(approvers) == 1
        assert approvers[0]["approver_id"] == chief_id
        assert approvers[0]["status"] == "pending"
    
    def test_承認者は承認待ち一覧を取得できる(self):
        """承認者は自分が承認すべき要件の一覧を取得できる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        org_id = system.create_organization("開発部", "department")
        chief_id = system.create_employee("鈴木課長", "課長", org_id)
        member1_id = system.create_employee("田中担当", "担当者", org_id)
        member2_id = system.create_employee("佐藤担当", "担当者", org_id)
        system.set_supervisor(member1_id, chief_id)
        system.set_supervisor(member2_id, chief_id)
        
        # Act
        req1_id = system.create_requirement("機能A", member1_id)
        req2_id = system.create_requirement("機能B", member2_id)
        pending = system.get_pending_approvals(chief_id)
        
        # Assert
        assert len(pending) == 2
        assert {p["req_id"] for p in pending} == {req1_id, req2_id}
    
    def test_高優先度要件は多段階承認が必要(self):
        """高優先度の要件は課長→部長の多段階承認が必要"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        org_id = system.create_organization("開発部", "department")
        manager_id = system.create_employee("山田部長", "部長", org_id)
        chief_id = system.create_employee("鈴木課長", "課長", org_id)
        member_id = system.create_employee("田中担当", "担当者", org_id)
        system.set_supervisor(member_id, chief_id)
        system.set_supervisor(chief_id, manager_id)
        
        # Act
        req_id = system.create_requirement("重要機能", member_id, priority="high")
        approvers = system.get_approvers(req_id)
        
        # Assert
        assert len(approvers) == 2
        assert approvers[0]["approver_id"] == chief_id
        assert approvers[0]["level"] == 1
        assert approvers[1]["approver_id"] == manager_id
        assert approvers[1]["level"] == 2
        assert approvers[1]["status"] == "waiting"  # 課長承認待ち
    
    def test_承認すると次の承認者が有効になる(self):
        """課長が承認すると部長の承認が有効になる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        org_id = system.create_organization("開発部", "department")
        manager_id = system.create_employee("山田部長", "部長", org_id)
        chief_id = system.create_employee("鈴木課長", "課長", org_id)
        member_id = system.create_employee("田中担当", "担当者", org_id)
        system.set_supervisor(member_id, chief_id)
        system.set_supervisor(chief_id, manager_id)
        req_id = system.create_requirement("重要機能", member_id, priority="high")
        
        # Act
        system.approve(req_id, chief_id, "問題ありません")
        approvers = system.get_approvers(req_id)
        
        # Assert
        chief_approval = next(a for a in approvers if a["approver_id"] == chief_id)
        manager_approval = next(a for a in approvers if a["approver_id"] == manager_id)
        assert chief_approval["status"] == "approved"
        assert manager_approval["status"] == "pending"  # waiting → pending
    
    def test_全承認完了で要件が承認済みになる(self):
        """全ての承認者が承認すると要件のステータスが承認済みになる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        org_id = system.create_organization("開発部", "department")
        chief_id = system.create_employee("鈴木課長", "課長", org_id)
        member_id = system.create_employee("田中担当", "担当者", org_id)
        system.set_supervisor(member_id, chief_id)
        req_id = system.create_requirement("機能追加", member_id)
        
        # Act
        system.approve(req_id, chief_id, "承認します")
        req_status = system.get_requirement_status(req_id)
        
        # Assert
        assert req_status == "approved"
    
    def test_却下すると要件が却下済みになる(self):
        """承認者が却下すると要件のステータスが却下済みになる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        org_id = system.create_organization("開発部", "department")
        chief_id = system.create_employee("鈴木課長", "課長", org_id)
        member_id = system.create_employee("田中担当", "担当者", org_id)
        system.set_supervisor(member_id, chief_id)
        req_id = system.create_requirement("機能追加", member_id)
        
        # Act
        system.reject(req_id, chief_id, "要件の見直しが必要")
        req_status = system.get_requirement_status(req_id)
        
        # Assert
        assert req_status == "rejected"


class TestRoleBasedAccessControl:
    """ロールベースアクセス制御の要件テスト"""
    
    def test_ユーザーにロールを付与できる(self):
        """ユーザーに対してロールを付与できる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        user_id = system.create_user("user001", "田中太郎")
        
        # Act
        system.assign_role(user_id, "editor")
        roles = system.get_user_roles(user_id)
        
        # Assert
        assert "editor" in roles
    
    def test_ロールに基づいてアクセス可否を判定できる(self):
        """ロールに基づいてリソースへのアクセス可否を判定できる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        user_id = system.create_user("user001", "田中太郎")
        system.assign_role(user_id, "editor")
        system.grant_permission_to_role("editor", "requirement", "edit")
        
        # Act
        can_edit = system.check_permission(user_id, "requirement", "edit")
        can_delete = system.check_permission(user_id, "requirement", "delete")
        
        # Assert
        assert can_edit is True
        assert can_delete is False
    
    def test_階層ロールで上位ロールは下位の権限を継承する(self):
        """管理者ロールは編集者ロールの権限も持つ"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        user_id = system.create_user("admin001", "管理者")
        system.assign_role(user_id, "admin")
        system.set_role_inheritance("admin", "editor")
        system.grant_permission_to_role("editor", "requirement", "edit")
        system.grant_permission_to_role("admin", "system", "manage")
        
        # Act
        can_edit = system.check_permission(user_id, "requirement", "edit")
        can_manage = system.check_permission(user_id, "system", "manage")
        
        # Assert
        assert can_edit is True  # 継承された権限
        assert can_manage is True  # 直接の権限
    
    def test_所有者は自分のリソースを編集できる(self):
        """リソースの所有者は権限に関係なく編集できる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        user_id = system.create_user("user001", "田中太郎")
        resource_id = system.create_resource("req001", "requirement", user_id)
        
        # Act
        can_edit = system.check_permission(user_id, resource_id, "edit")
        
        # Assert
        assert can_edit is True
    
    def test_部門内のリソースは同部門メンバーがアクセスできる(self):
        """同じ部門のメンバーはリソースにアクセスできる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        dept_id = system.create_department("開発部")
        user1_id = system.create_user("user001", "田中太郎")
        user2_id = system.create_user("user002", "佐藤次郎")
        system.assign_to_department(user1_id, dept_id)
        system.assign_to_department(user2_id, dept_id)
        
        resource_id = system.create_resource("req001", "requirement", user1_id)
        system.assign_resource_to_department(resource_id, dept_id)
        
        # Act
        can_view = system.check_permission(user2_id, resource_id, "view")
        
        # Assert
        assert can_view is True
    
    def test_一時的な権限を付与できる(self):
        """期限付きの一時的な権限を付与できる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        user_id = system.create_user("user001", "田中太郎")
        resource_id = system.create_resource("req001", "requirement", "other_user")
        expires_at = datetime.now() + timedelta(days=7)
        
        # Act
        system.grant_temporary_permission(user_id, resource_id, "edit", expires_at)
        can_edit_now = system.check_permission(user_id, resource_id, "edit")
        
        # Assert
        assert can_edit_now is True
    
    def test_権限を他のユーザーに委任できる(self):
        """自分の権限を他のユーザーに委任できる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        manager_id = system.create_user("manager001", "山田部長")
        deputy_id = system.create_user("deputy001", "代理者")
        system.assign_role(manager_id, "approver")
        
        # Act
        system.delegate_role(manager_id, deputy_id, "approver", days=7)
        can_approve = system.check_permission(deputy_id, "requirement", "approve")
        
        # Assert
        assert can_approve is True
    
    def test_権限の取得経路を説明できる(self):
        """なぜその権限を持っているかを説明できる"""
        # Arrange
        system = WorkflowPermissionSystem(":memory:")
        user_id = system.create_user("user001", "田中太郎")
        system.assign_role(user_id, "editor")
        system.grant_permission_to_role("editor", "requirement", "edit")
        
        # Act
        paths = system.explain_permission(user_id, "requirement", "edit")
        
        # Assert
        assert len(paths) > 0
        assert any("editor" in path for path in paths)


