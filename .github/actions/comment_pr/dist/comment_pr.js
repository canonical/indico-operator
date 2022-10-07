

module.exports = async (github, context, event) => {
    const fs = require('fs');
    const comments = JSON.parse(fs.readFileSync('report.json'));
    const issue_number = event.number
    console.log('The pull request: ${ event.pull_request }');
    console.log('The event payload: ${ event }');

    const createComment = async (body) => {
        await github.rest.issues.createComment({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: issue_number,
            body,
        });
    }
    
    const deleteGithubActionsComments = async () => {
        const existingComments = await github.rest.issues.listComments({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: issue_number,
        });
        const githubActionsComments = existingComments.data.filter(
            comment => comment.user.login == 'github-actions[bot]'
        )
        for (const comment of githubActionsComments) {
            await github.rest.issues.deleteComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: comment.id,
            });
        }
    }

    await deleteGithubActionsComments();
    for (const comment of comments) {
        await createComment(comment);
    }
}
