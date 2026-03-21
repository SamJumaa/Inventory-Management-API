class CompanyQuerySetMixin:
    def get_user_company(self):
        user = self.request.user
        if not user.is_authenticated:
            return None

        if hasattr(user, "profile"):
            return user.profile.company
        return None

    def get_queryset(self):
        queryset = super().get_queryset()
        company = self.get_user_company()

        if company is None:
            return queryset.none()

        return queryset.filter(company=company)

    def perform_create(self, serializer):
        company = self.get_user_company()
        serializer.save(company=company, created_by=self.request.user)
