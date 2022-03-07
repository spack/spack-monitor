# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from dal import autocomplete
from django.db.models import Q

from spackmon.apps.main.models import Spec


class SpecAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Spec.objects.all()

        # Filter based on name, version, full hash
        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q)
                | Q(version__icontains=self.q)
                | Q(full_hash__icontains=self.q)
            )
        return qs
