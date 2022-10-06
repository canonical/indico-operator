

module.exports = async ({github, context}) => {
    const core = require('@actions/core');
    const github = require('@actions/github');
    const fs = require('fs');
    const reports = JSON.parse(fs.readFileSync(`${core.getInput('artifact-name')}.json`));
    const issue_number = github.event.number;
    console.log(`The pull request: ${github.event.pull_request}`);
    console.log(`The event payload: ${github.event}`);

    const deleteGithubActionsComments = async () => {
        const comments = await github.rest.issues.listComments({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: issue_number,
        });
        const githubActionsComments = comments.data.filter(comment => comment.user.login == 'github-actions[bot]')
        for (const comment of githubActionsComments) {
            await github.rest.issues.deleteComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: issue_number,
            });
        }
    }

    await deleteGithubActionsComments();

    for (const report of reports) {
        await github.rest.issues.createComment({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: issue_number,
            r
        });
    }
}
