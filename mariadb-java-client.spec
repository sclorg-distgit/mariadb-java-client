%{?scl:%scl_package mariadb-java-client}
%{!?scl:%global pkg_name %{name}}

Name:		%{?scl_prefix}mariadb-java-client
Version:	2.7.1
Release:	1%{?dist}
Summary:	Connects applications developed in Java to MariaDB and MySQL databases
# added BSD license because of https://bugzilla.redhat.com/show_bug.cgi?id=1291558#c13
License:	BSD and LGPLv2+
URL:		https://mariadb.com/kb/en/mariadb/about-mariadb-connector-j/
Source0:	https://github.com/MariaDB/mariadb-connector-j/archive/%{version}.tar.gz
Source1:        artifact-jna.xml

# optional dependency not in Fedora
Patch0:		remove_waffle-jna.patch
Patch1:         remove-NamedPipeSocket.patch

BuildArch:	noarch
BuildRequires:	%{?scl_prefix_maven}maven-local
BuildRequires:	%{?scl_prefix_maven}mvn(com.google.code.maven-replacer-plugin:replacer)
BuildRequires:	%{?scl_prefix_maven}mvn(org.apache.felix:maven-bundle-plugin)
BuildRequires:	%{?scl_prefix_maven}mvn(org.codehaus.mojo:build-helper-maven-plugin)
BuildRequires:	%{?scl_prefix_maven}mvn(junit:junit)
BuildRequires:	%{?scl_prefix_maven}mvn(org.slf4j:slf4j-api)
BuildRequires:  %{?scl_prefix_maven}mvn(org.osgi:osgi.cmpn)
BuildRequires:  %{?scl_prefix_maven}mvn(org.osgi:osgi.core)
BuildRequires:	%{?scl_prefix}jna
# jna-platform is not found by mvn macro
#BuildRequires:	mvn(net.java.dev.jna:jna-platform)
BuildRequires:	%{?scl_prefix}jna-contrib
# since version 1.5.2 missing optional dependency (windows)
#BuildRequires:	mvn(com.github.dblock.waffle:waffle-jna)

#Requires:	mariadb

%description
MariaDB Connector/J is a Type 4 JDBC driver, also known as the Direct to
Database Pure Java Driver. It was developed specifically as a lightweight
JDBC connector for use with MySQL and MariaDB database servers.

%package javadoc
Summary:	Javadoc for %{name}

%description javadoc
This package contains the API documentation for %{name}.

%prep
%setup -qn mariadb-connector-j-%{version}

# convert files from dos to unix line encoding
for file in README.md documentation/*.creole; do
 sed -i.orig 's|\r||g' $file
 touch -r $file.orig $file
 rm $file.orig
done

# remove missing optional dependency waffle-jna
%pom_remove_dep com.github.waffle:waffle-jna
#%pom_remove_dep com.zaxxer:HikariCP
%pom_remove_dep ch.qos.logback:logback-classic
%pom_remove_dep junit:junit
%pom_remove_dep com.amazonaws:aws-java-sdk-rds

# use latest OSGi implementation
%pom_change_dep -r :org.osgi.core org.osgi:osgi.core
%pom_change_dep -r :org.osgi.compendium org.osgi:osgi.cmpn

rm -r src/main/java/org/mariadb/jdbc/credential/aws

sed -i 's|org.osgi.compendium|osgi.cmpn|' pom.xml
# also remove the file using the removed plugin
rm -f src/main/java/org/mariadb/jdbc/internal/com/send/authentication/gssapi/WindowsNativeSspiAuthentication.java
# patch the sources so that the missing file is not making trouble
%patch0 -p1 -b .patch0
# not required since we have sclized recent jna package
#%%patch1 -p1

%mvn_file org.mariadb.jdbc:%{name} %{name}
%mvn_alias org.mariadb.jdbc:%{name} mariadb:mariadb-connector-java

%pom_remove_plugin org.apache.maven.plugins:maven-source-plugin
%pom_remove_plugin org.apache.maven.plugins:maven-javadoc-plugin
%pom_remove_plugin org.sonatype.plugins:nexus-staging-maven-plugin
%pom_remove_plugin org.apache.maven.plugins:maven-gpg-plugin
%pom_remove_plugin org.jacoco:jacoco-maven-plugin
%pom_remove_plugin com.coveo:fmt-maven-plugin

# remove preconfigured OSGi manifest file and generate OSGi manifest file
# with maven-bundle-plugin instead of using maven-jar-plugin
rm src/main/resources/META-INF/MANIFEST.MF
%pom_xpath_set "pom:packaging" bundle
%pom_xpath_set "pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-jar-plugin']/pom:configuration/pom:archive/pom:manifestFile" '${project.build.outputDirectory}/META-INF/MANIFEST.MF'
%pom_xpath_remove "pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-jar-plugin']/pom:configuration/pom:archive/pom:manifestEntries"

%pom_add_plugin org.apache.felix:maven-bundle-plugin:2.5.4 . '
<extensions>true</extensions>
<configuration>
  <instructions>
    <Bundle-SymbolicName>${project.groupId}</Bundle-SymbolicName>
    <Bundle-Name>MariaDB JDBC Client</Bundle-Name>
    <Bundle-Version>${project.version}.0</Bundle-Version>
    <Export-Package>org.mariadb.jdbc.*</Export-Package>
    <Import-Package>
      !com.sun.jna.*,
      javax.net;resolution:=optional,
      javax.net.ssl;resolution:=optional,
      javax.sql;resolution:=optional,
      javax.transaction.xa;resolution:=optional
    </Import-Package>
  </instructions>
</configuration>
<executions>
  <execution>
    <id>bundle-manifest</id>
    <phase>process-classes</phase>
    <goals>
      <goal>manifest</goal>
    </goals>
  </execution>
</executions>'
# not required since we have sclized recent jna package
#%%mvn_config resolverSettings/metadataRepositories/repository %{SOURCE1}

%build
# tests are skipped, while they require running application server
%mvn_build -f

%install
%mvn_install

%files -f .mfiles
%doc documentation/* README.md
%license LICENSE

%files javadoc -f .mfiles-javadoc
%license LICENSE

%changelog
* Thu Dec 10 2020 Honza Horak <hhorak@redhat.com> - 2.7.1-1
- Rebase to 2.7.1

* Tue May 21 2019 Jakub Janco <jjanco@redhat.com> - 2.4.1-2
- Rebuild against java fixed meta pkg

* Fri Apr 05 2019 Jakub Janco <jjanco@redhat.com> - 2.4.1-1
- new version

* Fri Feb 22 2019 Jakub Janco <jjanco@redhat.com> - 2.4.0-1
- new version

* Tue Jan 08 2019 Honza Horak <hhorak@redhat.com> - 2.3.0-2
- Rebuild for buildroot change

* Tue Dec 18 2018 Jakub Janco <jjanco@redhat.com> - 2.3.0-1
- new version

* Tue Dec 18 2018 Jakub Janco <jjanco@redhat.com> - 2.2.6-2
- add missing build dependencies

* Fri Aug 10 2018 Jakub Janco <jjanco@redhat.com> - 2.2.6-1
- new version and SCL-izing spec

* Thu Jun 14 2018 Jakub Janco <jjanco@redhat.com> - 2.2.5-1
- update version

* Mon May 28 2018 Michael Simacek <msimacek@redhat.com> - 2.2.3-2
- Remove BR on maven-javadoc-plugin

* Tue Mar 13 2018 Jakub Janco <jjanco@redhat.com> - 2.2.3-1
- update version

* Mon Feb 26 2018 Jakub Janco <jjanco@redhat.com> - 2.2.2-1
- update version

* Thu Feb 08 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.2.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jan 03 2018 Jakub Janco <jjanco@redhat.com> - 2.2.1-1
- Update to 2.2.1

* Tue Nov 21 2017 Jakub Janco <jjanco@redhat.com> - 2.2.0-1
- Update to 2.2.0

* Tue Aug 29 2017 Tomas Repik <trepik@redhat.com> - 2.1.0-1
- Update to 2.1.0

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.0.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jun 26 2017 Tomas Repik <trepik@redhat.com> - 2.0.2-1
- version update

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 28 2016 Tomas Repik <trepik@redhat.com> - 1.5.5-1
- version update

* Mon Oct 03 2016 Tomas Repik <trepik@redhat.com> - 1.5.3-1
- version update

* Wed Sep 14 2016 Tomas Repik <trepik@redhat.com> - 1.5.2-1
- version update

* Tue Jun 21 2016 Tomas Repik <trepik@redhat.com> - 1.4.6-1
- version update

* Mon Apr 18 2016 Tomas Repik <trepik@redhat.com> - 1.4.2-1
- version update

* Wed Mar 23 2016 Tomas Repik <trepik@redhat.com> - 1.3.7-1
- version update
- BSD license added
- cosmetic updates in prep phase

* Thu Mar 10 2016 Tomas Repik <trepik@redhat.com> - 1.3.6-1
- version update

* Mon Feb 15 2016 Tomas Repik <trepik@redhat.com> - 1.3.5-1
- version update

* Wed Jan 20 2016 Tomáš Repík <trepik@redhat.com> - 1.3.3-3
- generating OSGi manifest file with maven-bundle-plugin

* Wed Dec 16 2015 Tomáš Repík <trepik@redhat.com> - 1.3.3-2
- installing LICENSE added
- conversion from dos to unix line encoding revised
- unnecessary tasks removed

* Wed Dec  9 2015 Tomáš Repík <trepik@redhat.com> - 1.3.3-1
- Initial package
