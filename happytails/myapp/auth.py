from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class KeycloakOIDCAuthenticationBackend(OIDCAuthenticationBackend):
 
    def get_userinfo(self, access_token, id_token, payload):
        return payload

    def create_user(self, claims):
        email = claims.get('email', '')
        username = claims.get('preferred_username', email)
        user = self.UserModel.objects.create_user(username, email)
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()

        return user

    def update_user(self, user, claims):
        user.email = claims.get('email', user.email)
        user.first_name = claims.get('given_name', user.first_name)
        user.last_name = claims.get('family_name', user.last_name)
        preferred_username = claims.get('preferred_username')
        if preferred_username and preferred_username != user.username:
            user.username = preferred_username

        user.save()
        return user

    def authenticate(self, request, **kwargs):
        user = super().authenticate(request, **kwargs)

        if user and request:
            id_token = request.session.get('oidc_id_token')

            if id_token:
                import base64
                import json

                try:
                    parts = id_token.split('.')
                    if len(parts) == 3:
                        payload = parts[1]
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.urlsafe_b64decode(payload)
                        claims = json.loads(decoded)

                        request.session['oidc_id_token_claims'] = claims

                        all_roles = set()

                        direct_roles = claims.get('roles', [])
                        if isinstance(direct_roles, list):
                            all_roles.update(direct_roles)

                        realm_roles = claims.get('realm_access', {}).get('roles', [])
                        all_roles.update(realm_roles)

                        resource_access = claims.get('resource_access', {})
                        for client_data in resource_access.values():
                            all_roles.update(client_data.get('roles', []))

                        request.session['user_roles'] = list(all_roles)
                        request.session.modified = True

                except Exception as e:
                    print(f"Error decoding token: {e}")

        return user
