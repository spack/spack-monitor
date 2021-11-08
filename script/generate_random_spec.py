#!/usr/bin/env spack-python

# This is a modified version derived from
# https://github.com/spack/spack-buildspace-exploration
# Instead of attempting the build, we just save the spec to the filesystem.
# The spec can then be used as test input for database development

import spack
import spack.architecture
import spack.cmd
import spack.compilers
import spack.config
import spack.dependency
import spack.directives
import spack.error
import spack.spec
import spack.package
import spack.package_prefs
import spack.repo
import spack.variant
import sys
import spack.solver.asp
import spack.version as vn

import os
import re
import subprocess as sp


possible_virtuals = None


class DepInfo:
    """Class to store the depedency information, which specifies the constraints."""

    def __init__(self, vertex):
        self.vertex = vertex
        self.constraints = []

    def add_constraints(self, constraint):
        self.constraints.append(constraint)

    def print_info(self):
        self.vertex.print_node()


class Vertex:
    """Class to keep track of the package as a node."""

    def __init__(self, name, pkg):
        self.name = name
        self.pkg = pkg
        # obtain the different versions available for this pkg, which will be used to
        # explore the space
        self.possible_versions = set()

        # deps is a dictionary containing all the dependencies for this pkg node
        # it could also be just a list of DepInfo instead of a dictionary
        self.deps = {}

        # keep track of number of parents
        self.num_parents = 0
        # parents left to be assigned a spec
        self.parents_left = 0
        # keep track of whether this pkg has been visited in the search
        self.visited = False
        self.spec_assigned = False
        self.constrained_cond = True
        # flag to  indicate whether this pkg node is removed form the space
        self.removed = False
        # keep track of number of parents removed from the space due to constraints
        # not being met during space exploration
        self.parents_removed = 0

    def insert(self, childvertex, constraints=None):
        """Insert child dependency pkg to this pkg node."""

        if self.deps.get(childvertex.name) is None:
            self.deps[childvertex.name] = DepInfo(childvertex)
            childvertex.num_parents = childvertex.num_parents + 1
            childvertex.parents_left = childvertex.parents_left + 1

        self.deps[childvertex.name].add_constraints(constraints)

        # if constrains have some version or variant conditions, then
        # set the flag in the child. This is to indicate that the pkg will be
        # explored in the space depending on whether the constraints were satisfied.
        for cond, dep in sorted(constraints.items()):
            named_cond = cond.copy()
            if named_cond.versions and named_cond.versions != vn.VersionList(":"):
                # childvertex.constrained_cond = True
                print(
                    f"child {childvertex.name} has version constraints {named_cond} for pkg {self.name}"
                )
            elif named_cond.variants:
                # childvertex.constrained_cond = True
                print(
                    f"child {childvertex.name} has variant constraints {named_cond} for pkg {self.name}"
                )
            else:
                childvertex.constrained_cond = False

    def print_node(self):
        if not self.visited:
            self.visited = True
            # print(f'{self.name} : numparents : {self.num_parents} deps {len(self.deps)}')
            for k, child in self.deps.items():
                child.print_info()

    def reset_visited(self):
        self.visited = False
        for k, child in self.deps.items():
            child.vertex.reset_visited()


class DepGraph:
    """Contains the whole dependency graph for a package.
    We will start by getting all the possible packages  and creating a graph
    out of it. As the space gets explored and spec gets assigned to each
    package, the space will be pruned and nodes will be removed from the
    dependency graph.
    """

    def __init__(self):
        # dictionary containing <pkg_name, pkg_node>
        self.node_collection = {}
        self.root = None

    def create_deps_graph(self, args):
        specs = spack.cmd.parse_specs(args)
        # print(f'Checking package spec {specs}')
        # check_packages_exist(specs)

        possible_virtuals = set(x.name for x in specs if x.virtual)
        possible = spack.package.possible_dependencies(
            *specs, virtuals=possible_virtuals, deptype=spack.dependency.all_deptypes
        )
        # get the list of all possible packages
        pkgs = set(possible)
        print(f"Total possible packages : {len(pkgs)} - packages {pkgs}")

        possible_packages = {}

        for pkg_name in sorted(pkgs):
            pkg = spack.repo.get(pkg_name)
            possible_packages[pkg_name] = pkg
            node = Vertex(pkg_name, pkg)
            self.node_collection[pkg_name] = node

        for pkg_name in sorted(pkgs):
            vertex = self.node_collection[pkg_name]
            pkg = possible_packages[pkg_name]
            for v in pkg.versions:
                vertex.possible_versions.add(v)

            # iterate over the package dependencies and add the children to the
            # dependency graph.
            for name, conditions in sorted(pkg.dependencies.items()):
                if self.node_collection.get(name) is None:
                    print(f"{name} is not in the node collection")
                    # print('Cannot handle virtual dependencies yet')
                else:
                    deps_vertex = self.node_collection[name]
                    vertex.insert(deps_vertex, conditions)

        self.root = self.node_collection[args]
        self.root.constrained_cond = False

    def print_graph(self):
        self.root.print_node()


class SampleSpace(object):
    def __init__(self, dep_graph):
        self.dep_graph = dep_graph
        self.node_collection = dep_graph.node_collection

    def check_to_remove(self, node):
        """
        Check if a node can be removed from the space. This happens when the
        constraints are not met, at which point that node is removed from the
        exploration space.
        """
        if node.removed:
            return False

        if node.parents_removed == node.num_parents:
            return True

        return False

    def remove_node_from_space(self, node):
        """
        Remove the node from the space. This happens when the parents are moved and
        the dependency was such that constraints caused this node to also be removed
        from the space.
        """
        if node.removed:
            return

        if node.parents_removed != node.num_parents:
            return

        node.removed = True
        # print(f'    {node.name} is removed from the space')
        for k, child in node.deps.items():
            child.vertex.parents_left = child.vertex.parents_left - 1
            child.vertex.parents_removed = child.vertex.parents_removed + 1

            # check if removing the parent leads to the removal of the child
            if self.check_to_remove(child.vertex):
                self.remove_node_from_space(child.vertex)
            # print(f'    {k} parent {node.name} decrement parents left : {child.vertex.parents_left}')

    def check_constraint_satisfied(self, node):
        if node.constrained_cond:
            return False

        return True

    def get_next_node(self):

        # iterate over all the nodes in the collection and do the following:
        # 1. If the node is not removed and all the parents have been assigned and
        # this node has not been assigned a spec, then do the following steps
        # 2. Remove nodes that should be removed.
        # 3. Check if the parents have taken a spec value that activates this node.
        # 4. And if not, then remove this node as there are constraints are not
        # satisfied to select this node.
        for name, node in self.node_collection.items():
            if not node.removed and node.parents_left == 0 and not node.spec_assigned:
                if self.check_to_remove(node):
                    self.remove_node_from_space(node)
                elif self.check_constraint_satisfied(node):
                    return node
                elif not node.removed:
                    # print(f'    {name} has no parents left to be assigned and version not assigned but constrained node')
                    self.remove_node_from_space(node)
        return None

    def select_version(self, node):
        if len(node.possible_versions) > 0:
            return node.name, list(node.possible_versions)[0]
        else:
            return node.name, None
        # print(f'***** ERROR cannot create a valid spec for {name} *****')

    def generate_root_spec(self):
        root_node = self.dep_graph.root
        root_spec = list()
        pkgname, version = self.select_version(root_node)
        if version is not None:
            print(f"Add build {pkgname} @ {version}")
            root_spec.append(f"{pkgname}@{version}")
        else:
            root_spec.append(f"{pkgname}")

        root_node.spec_assigned = True
        for k, child in root_node.deps.items():
            child.vertex.parents_left = child.vertex.parents_left - 1
            print(
                f"    {k} parent decrement parents left : {child.vertex.parents_left}"
            )

        return root_spec

    def generate_specs(self):

        # Generate the spec for the root package
        pkg_spec = self.generate_root_spec()

        # Get the next node that can have their version or variant assigned.
        node = self.get_next_node()
        # Spec assigned to valid dependencies
        deps_spec = list()
        while node is not None:
            pkgname, version = self.select_version(node)
            # TODO: Temporary hack for virtuals
            if pkgname == "pkgconf":
                print("skipping {pkgname}")
            else:
                if version is not None:
                    print(f"Add build {pkgname} @ {version}")
                    deps_spec.append(f"{pkgname}@{version}")
                else:
                    print(f"Add build{pkgname}")
                    deps_spec.append(f"{pkgname}")

            # Once the spec has been assigned for a node, release the children from
            # the dependency. This means decrement the parents left to be assigned
            # counter.
            node.spec_assigned = True
            for k, child in node.deps.items():
                child.vertex.parents_left = child.vertex.parents_left - 1

            for name, conditions in node.pkg.dependencies.items():
                for cond, dep in sorted(conditions.items()):
                    named_cond = cond.copy()
                    # As a first step we are only considering the case where version and
                    # variant constraint is none.
                    if (
                        named_cond.versions
                        and named_cond.versions != vn.VersionList(":")
                        and named_cond.versions != version
                    ):
                        print(f"wont include {name} due to {named_cond}")
                    elif named_cond.variants:
                        print(
                            f"wont include {name} due to variant constraint {named_cond}"
                        )
                    elif self.node_collection.get(name) is not None:
                        self.dep_graph.node_collection[name].constrained_cond = False
                        # print(f'{name} constrained condition turned to false')

            node = self.get_next_node()

        return pkg_spec, deps_spec


def generate_spec(pspec, output_dir):
    """Given a pspec (the main library and version dependencies) issue a
    command to spack on the command line to generate the spec in json,
    and save this spec to the user requested output file.
    """
    # name the output file based on the spec name
    output_file = os.path.join(
        output_dir, ("%s.json" % re.sub("( |^|@)", "-", pspec[0]).strip("-"))
    )

    # Note that we are generating with the full hash, which is the unique
    # identified for Spack Monitor
    process = sp.Popen(
        [
            "spack",
            "spec",
            "--json",
            "--hash-type",
            "full_hash",
            *pspec,
        ],
        stdout=sp.PIPE,
        stderr=sp.PIPE,
    )
    res = process.communicate()
    if process.returncode != 0:
        print(
            "This spec does not build:\n %s\n%s"
            % (res[0].decode("utf-8"), res[1].decode("utf-8"))
        )
    else:
        print("Success! Saving to %s" % output_file)
        with open(output_file, "w") as fd:
            fd.writelines(res[0].decode("utf-8"))


def main():

    # Count the arguments
    arguments = len(sys.argv) - 1

    if arguments < 2:
        sys.exit("Error: Pass in the package name and an output folder.")

    pkg_name = sys.argv[1]
    output_dir = os.path.abspath(sys.argv[2])
    if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
        sys.exit("Output directory must exist.")

    print(f"Generating configurations for {pkg_name}")

    dep_graph = DepGraph()
    dep_graph.create_deps_graph(pkg_name)
    dep_graph.print_graph()
    sampler = SampleSpace(dep_graph)
    pkg_spec, deps_spec = sampler.generate_specs()

    pkg_spec_str = "".join(pkg_spec)
    dspec_str = " ^".join(deps_spec)
    pspec = [f"{pkg_spec_str}", f"^{dspec_str}"]

    # Run the process, if it's successful, save to json file
    generate_spec(pspec, output_dir)


if __name__ == "__main__":
    main()
