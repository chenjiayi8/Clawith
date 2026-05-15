type JoinResult = {
    access_token?: string | null;
};

type UserLike = {
    tenant_id?: string | null;
};

type SyncInvitationJoinAuthParams<TUser extends UserLike> = {
    invitationCode: string | null;
    currentToken: string | null;
    joinCompany: (invitationCode: string) => Promise<JoinResult>;
    loadCurrentUser: () => Promise<TUser>;
    persistToken: (token: string) => void;
    applyAuth: (user: TUser, token: string) => void;
};

export async function syncAuthAfterInvitationJoin<TUser extends UserLike>({
    invitationCode,
    currentToken,
    joinCompany,
    loadCurrentUser,
    persistToken,
    applyAuth,
}: SyncInvitationJoinAuthParams<TUser>): Promise<boolean> {
    if (!invitationCode) {
        return false;
    }

    const joinRes = await joinCompany(invitationCode);
    const nextToken = joinRes.access_token || currentToken;

    if (joinRes.access_token) {
        persistToken(joinRes.access_token);
    }

    if (!nextToken) {
        return false;
    }

    const user = await loadCurrentUser();
    applyAuth(user, nextToken);
    return true;
}
