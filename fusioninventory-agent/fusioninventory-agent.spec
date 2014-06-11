Name:        fusioninventory-agent
Summary:     FusionInventory agent
Group:       Applications/System
License:     GPLv2+
URL:         http://fusioninventory.org/

Version:     2.3.8
Release:     1%{?dist}
Source0:     http://search.cpan.org/CPAN/authors/id/G/GR/GROUSSE/FusionInventory-Agent-%{version}%{?prever}.tar.gz

Source1:   %{name}.cron
Source2:   %{name}.init
Source3:   %{name}.service

Requires:  perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
BuildRequires: perl(inc::Module::Install)
BuildRequires: systemd

Requires:  perl-FusionInventory-Agent = %{version}-%{release}
%ifarch %{ix86} x86_64
Requires:  dmidecode
%endif

Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd

# excluding internal requires and windows stuff
%global __provides_exclude %{?__provides_exclude:__provides_exclude|}^perl\\(FusionInventory::
%global __requires_exclude %{?__requires_exclude:__requires_exclude|}^perl\\(FusionInventory::
%global __requires_exclude %__requires_exclude|^perl\\(Win32

%description
FusionInventory Agent is an application designed to help a network
or system administrator to keep track of the hardware and software
configurations of computers that are installed on the network.

This agent can send information about the computer to a OCS Inventory NG
or GLPI server with the FusionInventory for GLPI plugin.

You can add additional packages for optional tasks:

* perl-FusionInventory-Agent-Task-Network
    Network Discovery and Inventory support
* perl-Fusion-Inventory-Agent-Inventory
    Local inventory support for FusionInventory
* perl-FusionInventory-Agent-Task-Deploy
    Software deployment support
* perl-FusionInventory-Agent-Task-ESX
    vCenter/ESX/ESXi remote inventory
* perl-FusionInventory-WakeOnLan
    not included due to a licensing issue for perl-Net-Write

Edit the /etc/sysconfig/%{name} file for service configuration.

%package -n perl-FusionInventory-Agent
Summary:        Libraries for Fusioninventory agent
BuildArch:      noarch
Requires:       perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
Requires:       perl(LWP)
Requires:       perl(Net::CUPS)
Requires:       perl(Net::SSLeay)
Requires:       perl(Proc::Daemon)
Requires:       perl(Proc::PID::File)

%description -n perl-FusionInventory-Agent
Libraries for Fusioninventory agent.

%package task-esx
Summary:    FusionInventory plugin to inventory vCenter/ESX/ESXi
BuildArch:  noarch
Requires:   fusioninventory-agent = %{version}-%{release}

%description task-esx
fusioninventory-agent-task-ESX ask the running service agent to inventory an 
VMWare vCenter/ESX/ESXi server through SOAP interface

%package yum-plugin
Summary:       Ask FusionInventory agent to send an inventory when yum exits
Group:         System Environment/Base
BuildArch:     noarch
Requires:      yum
Requires:      %{name}

%description yum-plugin
fusioninventory-agent-yum-plugin asks the running service agent to send an
inventory when yum exits.

This requires the service to be running with the --rpc-trust-localhost option.

%package task-network
Summary:    NetDiscovery and NetInventory task for FusionInventory
Group:      Applications/System
BuildArch:      noarch
Requires:       fusioninventory-agent = %{version}-%{release}

%description task-network
fusioninventory-task-netdiscovery and fusioninventory-task-netinventory

%package task-deploy
Summary:    Software deployment support for FusionInventory agent
Group:      Applications/System
BuildArch:  noarch
Requires:   fusioninventory-agent = %{version}-%{release}
Requires:   perl(Archive::Extract)

%description task-deploy
This package provides software deployment support for FusionInventory-agent

#%package task-wakeonlan
#Summary:    WakeOnLan task for FusionInventory
#Group:      Applications/System
#BuildArch:  noarch
#Requires:   fusioninventory-agent = %{version}-%{release}

#%description task-wakeonlan
#fusioninventory-task-wakeonlan

%package task-inventory
Summary:    Inventory task for FusionInventory
Group:      Applications/System
BuildArch:  noarch
Requires:   fusioninventory-agent = %{version}-%{release}
Requires:   perl(Net::CUPS)
Requires:   perl(Parse::EDID)


%description task-inventory
fusioninventory-task-inventory
%prep
%setup -q -n FusionInventory-Agent-%{version}%{?prever}

# This work only on older version, and is ignored on recent
cat <<EOF | tee %{name}-req
#!/bin/sh
%{__perl_requires} $* |
sed -e '/perl(Win32/d'
EOF

%global __perl_requires %{_builddir}/FusionInventory-Agent-%{version}%{?prever}/%{name}-req
chmod +x %{__perl_requires}

cat <<EOF | tee logrotate
%{_localstatedir}/log/%{name}/*.log {
    weekly
    rotate 7
    compress
    notifempty
    missingok
}
EOF

cat <<EOF | tee %{name}.conf
#
# Fusion Inventory Agent Configuration File
# used by hourly cron job and service launcher to override the %{name}.cfg setup.
#
# DONT FORGET to enable the service !
#
# Add tools directory if needed (tw_cli, hpacucli, ipssend, ...)
PATH=/sbin:/bin:/usr/sbin:/usr/bin
# Global options (debug for verbose log, rpc-trust-localhost for yum-plugin)
FUSINVOPT="--debug --rpc-trust-localhost"
# Mode, change to "cron" or "daemon" to activate
# - none (default on install) no activity
# - cron (inventory only) use the cron.hourly
# NB systemd service launcher only use FUSINVOPT and agent.cfg
OCSMODE[0]=none
# OCS Inventory or FusionInventory server URI
# OCSSERVER[0]=your.ocsserver.name
# OCSSERVER[0]=http://your.ocsserver.name/ocsinventory
# OCSSERVER[0]=http://your.glpiserveur.name/glpi/plugins/fusioninventory/
# corresponds with --local=%{_localstatedir}/lib/%{name}
# OCSSERVER[0]=local
# Wait before inventory (for cron mode)
OCSPAUSE[0]=120
# Administrative TAG (optional, must be filed before first inventory)
OCSTAG[0]=
EOF


%build
perl Makefile.PL \
     PREFIX=%{_prefix} \
     SYSCONFDIR=%{_sysconfdir}/fusioninventory \
     LOCALSTATEDIR=%{_localstatedir}/lib/%{name}

make %{?_smp_mflags}


%install
rm -rf %{buildroot}

make install DESTDIR=%{buildroot}
find %{buildroot} -type f -name .packlist -exec rm -f {} ';'

%{_fixperms} %{buildroot}/*

mkdir -p %{buildroot}%{_localstatedir}/{log,lib}/%{name}

install -m 644 -D  logrotate     %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -m 644 -D  %{name}.conf  %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -m 755 -Dp %{SOURCE1}    %{buildroot}%{_sysconfdir}/cron.hourly/%{name}
install -m 644 -Dp %{SOURCE3}    %{buildroot}%{_unitdir}/%{name}.service


# Yum plugin installation
install -m 644 -D contrib/yum-plugin/%{name}.py   %{buildroot}%{_prefix}/lib/yum-plugins/%{name}.py
install -m 644 -D contrib/yum-plugin/%{name}.conf %{buildroot}%{_sysconfdir}/yum/pluginconf.d/%{name}.conf



%post
%systemd_post fusioninventory-agent.service


%preun
%systemd_preun fusioninventory-agent.service


%postun
%systemd_postun_with_restart fusioninventory-agent.service


%files
%dir %{_sysconfdir}/fusioninventory
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{_sysconfdir}/fusioninventory/agent.cfg
%{_sysconfdir}/cron.hourly/%{name}
%{_unitdir}/%{name}.service
%{_bindir}/fusioninventory-agent
%{_bindir}/fusioninventory-injector
%{_mandir}/man1/fusioninventory-agent*
%{_mandir}/man1/fusioninventory-injector*
%dir %{_localstatedir}/log/%{name}
%dir %{_localstatedir}/lib/%{name}
#excluding sub-packages files
%exclude %{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/



%files -n perl-FusionInventory-Agent
%doc Changes LICENSE THANKS
%{_datadir}/fusioninventory

%files yum-plugin
%config(noreplace) %{_sysconfdir}/yum/pluginconf.d/%{name}.conf
%{_prefix}/lib/yum-plugins/%{name}.*

%files task-esx
%{_bindir}/fusioninventory-esx
%{_mandir}/man1/fusioninventory-esx.1*
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/ESX.pm
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/SOAP

%files task-network
%{_bindir}/fusioninventory-netdiscovery
%{_bindir}/fusioninventory-netinventory
%{_mandir}/man1/fusioninventory-netdiscovery.1*
%{_mandir}/man1/fusioninventory-netinventory.1*
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/NetDiscovery.pm
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/NetInventory.pm

%files task-deploy
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Deploy.pm
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Deploy

# Excluding task-wakeonlan
#%files task-wakeonlan
%exclude %{_bindir}/fusioninventory-wakeonlan
%exclude %{_mandir}/man1/fusioninventory-wakeonlan.1*
%exclude %{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/WakeOnLan.pm

%files task-inventory
%{_bindir}/fusioninventory-inventory
%{_mandir}/man1/fusioninventory-inventory.1*
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Inventory.pm
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Inventory


%changelog
* Tue May 20 2014 Marianne Lombard <marianne@tuxette.fr> - 2.3.8-1
- enhancing spec according to Michael Schwendt review
- adding missing requires

* Fri May 16 2014 Marianne Lombard <marianne@tuxette.fr> - 2.3.8
- new version

* Wed May 14 2014 Marianne Lombard <marianne@tuxette.fr> - 2.3.7.1
- new version 

* Sat Feb 1 2014 Marianne Lombard <marianne@tuxette.fr> - 2.3.6
- new version, reintroduction in fedora and epel
- cleanup of the spec (removing sysVinit stuff, old BuildRequires, old releases stuff)
- adding sub-packages for task-* (using Guillaume Rousse OBS spec as model https://build.opensuse.org/package/view_file/home:guillomovitch/fusioninventory-agent/fusioninventory-agent.spec)
- task-wakeonlan is excluded (dependancy issue)

* Wed Aug  8 2012 Remi Collet <remi@fedoraproject.org> - 2.2.4-2
- dump release

* Wed Aug  8 2012 Remi Collet <remi@fedoraproject.org> - 2.2.4-1
- version 2.2.4 fixes various bugs as described in
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.2.4/Changes
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.2.3/Changes

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jun 25 2012 Petr Pisar <ppisar@redhat.com> - 2.2.2-4
- Perl 5.16 rebuild

* Tue Jun 05 2012 Remi Collet <remi@fedoraproject.org> - 2.2.2-3
- no need for debuginfo (not really arch, fix #828960)
- yum plugin is also noarch

* Thu May 31 2012 Remi Collet <remi@fedoraproject.org> - 2.2.2-2
- make package "arch"
- requires dmidecode when available (x86)
- add sub-package perl-FusionInventory-Agent (noarch)

* Wed May 30 2012 Remi Collet <remi@fedoraproject.org> - 2.2.2-1
- update to 2.2.2
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.2.2/Changes
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.2.1/Changes

* Fri May 11 2012 Remi Collet <remi@fedoraproject.org> - 2.2.0-2
- filter private provides/requires

* Thu May 10 2012 Remi Collet <remi@fedoraproject.org> - 2.2.0-1
- update to 2.2.0
  http://search.cpan.org/src/FUSINV/FusionInventory-Agent-2.2.0/Changes
- revert change in 2.2.0: don't loose arch information
  see http://forge.fusioninventory.org/issues/1581

* Sun Feb 26 2012 Remi Collet <remi@fedoraproject.org> - 2.1.14-1
- update to 2.1.14
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.14/Changes

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1.12-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Nov 28 2011 Remi Collet <remi@fedoraproject.org> - 2.1.12-1
- update to 2.1.12
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.12/Changes
- upstream patch for http://forge.fusioninventory.org/issues/1161

* Sat Aug 06 2011 Remi Collet <remi@fedoraproject.org> - 2.1.9-3
- adapt filter

* Mon Jul 25 2011 Petr Sabata <contyk@redhat.com> - 2.1.9-2
- Perl mass rebuild

* Sun Jun 26 2011 Remi Collet <Fedora@famillecollet.com> 2.1.9-1
- missing dist tag

* Wed Jun 15 2011 Remi Collet <Fedora@famillecollet.com> 2.1.9-1
- update to 2.1.9
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.9/Changes

* Sat Jun 11 2011 Remi Collet <Fedora@famillecollet.com> 2.1.9-0.1.git9bd1238
- update to 2.1.9 from git
- improved init script for systemd
- improved comment for use with glpi-fusioninventory

* Thu Mar 31 2011 Remi Collet <Fedora@famillecollet.com> 2.1.8-2
- revert change for issue 656 which breaks compatibility

* Wed Mar 30 2011 Remi Collet <Fedora@famillecollet.com> 2.1.8-1
- update to 2.1.8
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.8/Changes

* Thu Dec 30 2010 Remi Collet <Fedora@famillecollet.com> 2.1.7-2
- add the yum-plugin sub-package

* Mon Dec 13 2010 Remi Collet <Fedora@famillecollet.com> 2.1.7-1
- update to 2.1.7
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.7/Changes

* Sun Nov 28 2010 Remi Collet <Fedora@famillecollet.com> 2.1.7-0.1.beta1
- update to 2.1.7 beta1

* Sat Nov 13 2010 Remi Collet <Fedora@famillecollet.com> 2.1.6-1.1
- fix perl filter on EL-6

* Wed Oct 06 2010 Remi Collet <Fedora@famillecollet.com> 2.1.6-1
- update to 2.1.6
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.6/Changes
- fix init script for multi-server in daemon mode
- workaround for http://forge.fusioninventory.org/issues/414

* Wed Sep 15 2010 Remi Collet <Fedora@famillecollet.com> 2.1.5-1
- update to 2.1.5
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.5/Changes

* Fri Sep 10 2010 Remi Collet <Fedora@famillecollet.com> 2.1.3-2
- add %%check

* Sat Sep 04 2010 Remi Collet <Fedora@famillecollet.com> 2.1.3-1
- update to 2.1.3
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.3/Changes

* Wed Aug 25 2010 Remi Collet <Fedora@famillecollet.com> 2.1.2-1
- update to 2.1.2
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.2/Changes

* Wed Aug 18 2010 Remi Collet <Fedora@famillecollet.com> 2.1.1-1
- update to 2.1.1

* Wed Aug 18 2010 Remi Collet <Fedora@famillecollet.com> 2.1-2.gita7532c0
- update to git snaphost which fix EL issues
- fix init script
- adapt perl filter for recent/old fedora or EL

* Mon Aug 16 2010 Remi Collet <Fedora@famillecollet.com> 2.1-1
- update to 2.1
- switch download URL back to CPAN
- add %%{perl_vendorlib}/auto
- filter perl(Win32*) from Requires
- add patch (from git) to reopen the file logger if needed

* Sat May 29 2010 Remi Collet <Fedora@famillecollet.com> 2.0.6-1
- update to 2.0.6
- swicth download URL to forge

* Wed May 12 2010 Remi Collet <Fedora@famillecollet.com> 2.0.5-1
- update to 2.0.5

* Tue May 11 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-4.gitf7c5492
- git snapshot fix perl 5.8.8 (EL5) issue

* Sat May 08 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-4.gitddfdeaf
- git snapshot fix daemon issue
- add FUSINVOPT for global options (p.e.--debug)

* Sat May 08 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-3
- add support for daemon mode

* Fri May 07 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-2
- info about perl-FusionInventory-Agent-Task-OcsDeploy
- spec cleanup
- french translation
- set Net::CUPS and Archive::Extract optionnal on RHEL4

* Fri May 07 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-1
- update to 2.0.4 which fixes important bugs when cron is used

* Sat May 01 2010 Remi Collet <Fedora@famillecollet.com> 2.0.3-1
- initial spec

