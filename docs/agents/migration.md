# Migration and release scope

The archive boundary begins with the first fully confirmed PyPI release.
Select a cataloged version for its immutable API documentation; dev describes source.
A GitHub tag or successful build alone is not proof of registry availability.

After publication, use the exact version's installation page and API reference.
Pre-1.0 breaking changes increment the minor version; features also increment the
minor version; fixes increment the patch. Review the release changelog. Releases now run automatically from main; manual
workflow dispatch can supply an exact version.
No automatic input translation or compatibility layer is planned.

To change deployments, create a new client, re-read capabilities/guidance and resolve
new asset/voice IDs. Do not reuse cached IDs across servers. The transport contract
stays shared, but valid model-native inputs can change. Legacy engine integrations
must move to a server adapter before this client can replace them.
