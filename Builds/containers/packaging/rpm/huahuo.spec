%define dcf_version %(echo $dcf_RPM_VERSION)
%define rpm_release %(echo $RPM_RELEASE)
%define rpm_patch %(echo $RPM_PATCH)
%define _prefix /opt/ripple
Name:           dcf
# Dashes in Version extensions must be converted to underscores
Version:        %{dcf_version}
Release:        %{rpm_release}%{?dist}%{rpm_patch}
Summary:        dcf daemon

License:        MIT
URL:            http://ripple.com/
Source0:        dcf.tar.gz
Source1:        validator-keys.tar.gz

BuildRequires:  protobuf-static openssl-static cmake zlib-static ninja-build

%description
dcf

%package devel
Summary: Files for development of applications using xrpl core library
Group: Development/Libraries
Requires: openssl-static, zlib-static

%description devel
core library for development of standalone applications that sign transactions.

%prep
%setup -c -n dcf -a 1

%build
cd dcf
mkdir -p bld.release
cd bld.release
cmake .. -G Ninja -DCMAKE_INSTALL_PREFIX=%{_prefix} -DCMAKE_BUILD_TYPE=Release -Dstatic=true -DCMAKE_VERBOSE_MAKEFILE=ON -Dlocal_protobuf=ON
# build VK
cd ../../validator-keys-tool
mkdir -p bld.release
cd bld.release
# Install a copy of the dcf artifacts into a local VK build dir so that it
# can use them to build against (VK needs xrpl_core lib to build). We install
# into a local build dir instead of buildroot because we want VK to have
# relative paths embedded in debug info, otherwise check-buildroot (rpmbuild)
# will complain
mkdir xrpl_dir
DESTDIR="%{_builddir}/validator-keys-tool/bld.release/xrpl_dir"  cmake --build ../../dcf/bld.release --target install -- -v
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=%{_builddir}/validator-keys-tool/bld.release/xrpl_dir/opt/ripple -Dstatic=true -DCMAKE_VERBOSE_MAKEFILE=ON
cmake --build . --parallel -- -v

%pre
test -e /etc/pki/tls || { mkdir -p /etc/pki; ln -s /usr/lib/ssl /etc/pki/tls; }

%install
rm -rf $RPM_BUILD_ROOT
DESTDIR=$RPM_BUILD_ROOT cmake --build dcf/bld.release --target install -- -v
install -d ${RPM_BUILD_ROOT}/etc/opt/ripple
install -d ${RPM_BUILD_ROOT}/usr/local/bin
ln -s %{_prefix}/etc/dcf.cfg ${RPM_BUILD_ROOT}/etc/opt/ripple/dcf.cfg
ln -s %{_prefix}/etc/validators.txt ${RPM_BUILD_ROOT}/etc/opt/ripple/validators.txt
ln -s %{_prefix}/bin/dcf ${RPM_BUILD_ROOT}/usr/local/bin/dcf
install -D validator-keys-tool/bld.release/validator-keys ${RPM_BUILD_ROOT}%{_bindir}/validator-keys
install -D ./dcf/Builds/containers/shared/dcf.service ${RPM_BUILD_ROOT}/usr/lib/systemd/system/dcf.service
install -D ./dcf/Builds/containers/packaging/rpm/50-dcf.preset ${RPM_BUILD_ROOT}/usr/lib/systemd/system-preset/50-dcf.preset
install -D ./dcf/Builds/containers/shared/update-dcf.sh ${RPM_BUILD_ROOT}%{_bindir}/update-dcf.sh
install -D ./dcf/Builds/containers/shared/update-dcf-cron ${RPM_BUILD_ROOT}%{_prefix}/etc/update-dcf-cron
install -D ./dcf/Builds/containers/shared/dcf-logrotate ${RPM_BUILD_ROOT}/etc/logrotate.d/dcf
install -d $RPM_BUILD_ROOT/var/log/dcf
install -d $RPM_BUILD_ROOT/var/lib/dcf

%post
USER_NAME=dcf
GROUP_NAME=dcf

getent passwd $USER_NAME &>/dev/null || useradd $USER_NAME
getent group $GROUP_NAME &>/dev/null || groupadd $GROUP_NAME

chown -R $USER_NAME:$GROUP_NAME /var/log/dcf/
chown -R $USER_NAME:$GROUP_NAME /var/lib/dcf/
chown -R $USER_NAME:$GROUP_NAME %{_prefix}/

chmod 755 /var/log/dcf/
chmod 755 /var/lib/dcf/

chmod 644 %{_prefix}/etc/update-dcf-cron
chmod 644 /etc/logrotate.d/dcf
chown -R root:$GROUP_NAME %{_prefix}/etc/update-dcf-cron

%files
%doc dcf/README.md dcf/LICENSE
%{_bindir}/dcf
/usr/local/bin/dcf
%{_bindir}/update-dcf.sh
%{_prefix}/etc/update-dcf-cron
%{_bindir}/validator-keys
%config(noreplace) %{_prefix}/etc/dcf.cfg
%config(noreplace) /etc/opt/ripple/dcf.cfg
%config(noreplace) %{_prefix}/etc/validators.txt
%config(noreplace) /etc/opt/ripple/validators.txt
%config(noreplace) /etc/logrotate.d/dcf
%config(noreplace) /usr/lib/systemd/system/dcf.service
%config(noreplace) /usr/lib/systemd/system-preset/50-dcf.preset
%dir /var/log/dcf/
%dir /var/lib/dcf/

%files devel
%{_prefix}/include
%{_prefix}/lib/*.a
%{_prefix}/lib/cmake/ripple

%changelog
* Wed May 15 2019 Mike Ellery <mellery451@gmail.com>
- Make validator-keys use local dcf build for core lib

* Wed Aug 01 2018 Mike Ellery <mellery451@gmail.com>
- add devel package for signing library

* Thu Jun 02 2016 Brandon Wilson <bwilson@ripple.com>
- Install validators.txt

